from typing import cast, Sequence, Union

import nnabla as nn

import nnabla_rl.functions as RNF
from nnabla_rl.models import QFunction, VFunction, StochasticPolicy, Model
from nnabla_rl.model_trainers.model_trainer import Training, TrainingVariables
from nnabla_rl.utils.data import convert_to_list_if_not_list


class _VFunctionSoftVTraining(Training):
    _target_functions: Sequence[QFunction]
    _target_policy: StochasticPolicy

    def __init__(self,
                 target_functions: Sequence[QFunction],
                 target_policy: StochasticPolicy):
        self._target_functions = target_functions
        self._target_policy = target_policy

    def compute_target(self, training_variables: TrainingVariables, **kwargs):
        s_current = training_variables.s_current

        policy_distribution = self._target_policy.pi(s_current)
        sampled_action, log_pi = policy_distribution.sample_and_compute_log_prob()

        q_values = []
        for q_function in self._target_functions:
            q_values.append(q_function.q(s_current, sampled_action))
        target_q = RNF.minimum_n(q_values)

        return target_q - log_pi


class SoftVTraining(Training):
    _delegate: Training

    def __init__(self,
                 train_functions: Union[Sequence[Model], Model],
                 target_functions: Union[Sequence[Model], Model],
                 target_policy: StochasticPolicy):
        super(SoftVTraining, self).__init__()
        train_functions = convert_to_list_if_not_list(train_functions)
        target_functions = convert_to_list_if_not_list(target_functions)
        train_function = train_functions[0]
        target_function = target_functions[0]
        if isinstance(train_function, VFunction) and isinstance(target_function, QFunction):
            target_functions = cast(Sequence[QFunction], target_functions)
            self._delegate = _VFunctionSoftVTraining(target_functions, target_policy)
        else:
            raise NotImplementedError(f'No training implementation for class: {train_function.__class__}')

    def compute_target(self, training_variables: TrainingVariables, **kwargs) -> nn.Variable:
        return self._delegate.compute_target(training_variables, **kwargs)
