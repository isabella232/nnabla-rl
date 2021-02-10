# Copyright (c) 2021 Sony Corporation. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import nnabla as nn
import nnabla.solvers as NS

from dataclasses import dataclass

import numpy as np

import gym
from typing import Union

import nnabla_rl.environment_explorers as EE
import nnabla_rl.model_trainers as MT
from nnabla_rl.environment_explorer import EnvironmentExplorer
from nnabla_rl.environments.environment_info import EnvironmentInfo
from nnabla_rl.algorithm import Algorithm, AlgorithmConfig, eval_api
from nnabla_rl.builders import StochasticPolicyBuilder, SolverBuilder
from nnabla_rl.replay_buffer import ReplayBuffer
from nnabla_rl.utils.data import marshall_experiences
from nnabla_rl.models import StochasticPolicy, REINFORCEContinousPolicy, REINFORCEDiscretePolicy
from nnabla_rl.model_trainers.model_trainer import ModelTrainer, TrainingBatch


@dataclass
class REINFORCEConfig(AlgorithmConfig):
    reward_scale: float = 0.01
    num_rollouts_per_train_iteration: int = 10
    learning_rate: float = 1e-3
    clip_grad_norm: float = 1.0
    # this parameter is not used in discrete environment
    fixed_ln_var: float = np.log(0.1)

    def __post_init__(self):
        '''__post_init__

        Check the set values are in valid range.

        '''
        self._assert_positive(self.reward_scale, 'reward_scale')
        self._assert_positive(self.num_rollouts_per_train_iteration, 'num_rollouts_per_train_iteration')
        self._assert_positive(self.learning_rate, 'learning_rate')
        self._assert_positive(self.clip_grad_norm, 'clip_grad_norm')


class DefaultPolicyBuilder(StochasticPolicyBuilder):
    def build_model(self,  # type: ignore[override]
                    scope_name: str,
                    env_info: EnvironmentInfo,
                    algorithm_config: REINFORCEConfig,
                    **kwargs) -> StochasticPolicy:
        if env_info.is_discrete_action_env():
            return self._build_discrete_policy(scope_name, env_info, algorithm_config)
        else:
            return self._build_continuous_policy(scope_name, env_info, algorithm_config)

    def _build_continuous_policy(self,
                                 scope_name: str,
                                 env_info: EnvironmentInfo,
                                 algorithm_config: REINFORCEConfig,
                                 **kwargs) -> StochasticPolicy:
        return REINFORCEContinousPolicy(scope_name, env_info.action_dim, algorithm_config.fixed_ln_var)

    def _build_discrete_policy(self,
                               scope_name: str,
                               env_info: EnvironmentInfo,
                               algorithm_config: REINFORCEConfig,
                               **kwargs) -> StochasticPolicy:
        return REINFORCEDiscretePolicy(scope_name, env_info.action_dim)


class DefaultSolverBuilder(SolverBuilder):
    def build_solver(self,  # type: ignore[override]
                     env_info: EnvironmentInfo,
                     algorithm_config: REINFORCEConfig,
                     **kwargs) -> nn.solver.Solver:
        return NS.Adam(alpha=algorithm_config.learning_rate)


class REINFORCE(Algorithm):
    _config: REINFORCEConfig
    _policy: StochasticPolicy
    _policy_solver: nn.solver.Solver

    _environment_explorer: EnvironmentExplorer
    _policy_trainer: ModelTrainer

    _eval_state_var: nn.Variable
    _eval_action: nn.Variable

    def __init__(self,
                 env_or_env_info: Union[gym.Env, EnvironmentInfo],
                 config: REINFORCEConfig = REINFORCEConfig(),
                 policy_builder: StochasticPolicyBuilder = DefaultPolicyBuilder(),
                 policy_solver_builder: SolverBuilder = DefaultSolverBuilder()):
        super(REINFORCE, self).__init__(env_or_env_info, config=config)
        self._policy = policy_builder("pi", self._env_info, self._config)
        self._policy_solver = policy_solver_builder(self._env_info, self._config)

    @eval_api
    def compute_eval_action(self, s):
        action, _ = self._compute_action(s)
        return action

    def _before_training_start(self, env_or_buffer):
        self._environment_explorer = self._setup_environment_explorer(env_or_buffer)
        self._policy_trainer = self._setup_policy_training(env_or_buffer)

    def _setup_environment_explorer(self, env_or_buffer):
        if self._is_buffer(env_or_buffer):
            return None
        explorer_config = EE.RawPolicyExplorerConfig(
            reward_scalar=self._config.reward_scale,
            initial_step_num=self.iteration_num,
            timelimit_as_terminal=False
        )
        explorer = EE.RawPolicyExplorer(policy_action_selector=self._compute_action,
                                        env_info=self._env_info,
                                        config=explorer_config)
        return explorer

    def _setup_policy_training(self, env_or_buffer):
        policy_trainer_config = MT.policy_trainers.SPGPolicyTrainerConfig(
            pi_loss_scalar=1.0 / self._config.num_rollouts_per_train_iteration,
            grad_clip_norm=self._config.clip_grad_norm)
        policy_trainer = MT.policy_trainers.SPGPolicyTrainer(
            env_info=self._env_info,
            config=policy_trainer_config)

        training = MT.policy_trainings.REINFORCETraining()
        policy_trainer.setup_training(self._policy, {self._policy.scope_name: self._policy_solver}, training)
        return policy_trainer

    def _run_online_training_iteration(self, env):
        buffer = ReplayBuffer(capacity=self._config.num_rollouts_per_train_iteration)

        for _ in range(self._config.num_rollouts_per_train_iteration):
            experience = self._environment_explorer.rollout(env)
            buffer.append(experience)

        self._reinforce_training(buffer)

    def _run_offline_training_iteration(self, buffer):
        raise NotImplementedError

    def _reinforce_training(self, buffer):
        # sample all experience in the buffer
        experiences, *_ = buffer.sample(buffer.capacity)
        s_batch, a_batch, target_return = self._align_experiences_and_compute_accumulated_reward(experiences)
        extra = {}
        extra['target_return'] = target_return
        batch = TrainingBatch(batch_size=len(s_batch),
                              s_current=s_batch,
                              a_current=a_batch,
                              extra=extra)

        self._policy_trainer.train(batch)

    def _align_experiences_and_compute_accumulated_reward(self, experiences):
        s_batch = None
        a_batch = None
        accumulated_reward_batch = None

        for experience in experiences:
            s_seq, a_seq, r_seq, *_ = marshall_experiences(experience)
            accumulated_reward = np.cumsum(r_seq[::-1])[::-1]

            if s_batch is None:
                s_batch = s_seq
                a_batch = a_seq
                accumulated_reward_batch = accumulated_reward
                continue

            s_batch = np.concatenate((s_batch, s_seq), axis=0)
            a_batch = np.concatenate((a_batch, a_seq), axis=0)
            accumulated_reward_batch = np.concatenate(
                (accumulated_reward_batch, accumulated_reward))

        return s_batch, a_batch, accumulated_reward_batch

    def _compute_action(self, s):
        s = np.expand_dims(s, axis=0)
        if not hasattr(self, '_eval_state_var'):
            self._eval_state_var = nn.Variable(s.shape)
            distribution = self._policy.pi(self._eval_state_var)
            self._eval_action = distribution.sample()
        self._eval_state_var.d = s
        self._eval_action.forward()
        return np.squeeze(self._eval_action.d, axis=0), {}

    def _models(self):
        models = {}
        models[self._policy.scope_name] = self._policy
        return models

    def _solvers(self):
        solvers = {}
        solvers[self._policy.scope_name] = self._policy_solver
        return solvers

    @property
    def latest_iteration_state(self):
        latest_iteration_state = {}
        latest_iteration_state['scalar'] = {}
        latest_iteration_state['histogram'] = {}
        return latest_iteration_state
