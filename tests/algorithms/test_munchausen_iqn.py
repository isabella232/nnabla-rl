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

import pytest

import nnabla as nn

import numpy as np

from nnabla_rl.replay_buffer import ReplayBuffer
import nnabla_rl.environments as E
import nnabla_rl.algorithms as A


class TestMunchausenIQN(object):
    def setup_method(self, method):
        nn.clear_parameters()

    def test_algorithm_name(self):
        dummy_env = E.DummyDiscreteImg()
        m_iqn = A.MunchausenIQN(dummy_env)

        assert m_iqn.__name__ == 'MunchausenIQN'

    def test_run_online_training(self):
        '''
        Check that no error occurs when calling online training
        '''

        dummy_env = E.DummyDiscreteImg()
        config = A.MunchausenIQNConfig()
        config.start_timesteps = 5
        config.batch_size = 5
        config.learner_update_frequency = 1
        config.target_update_frequency = 1
        m_iqn = A.MunchausenIQN(dummy_env, config=config)

        m_iqn.train_online(dummy_env, total_iterations=5)

    def test_run_offline_training(self):
        dummy_env = E.DummyDiscreteImg()
        batch_size = 5
        config = A.MunchausenIQNConfig()
        config.batch_size = batch_size
        config.learner_update_frequency = 1
        config.target_update_frequency = 1

        m_iqn = A.MunchausenIQN(dummy_env, config=config)

        experiences = generate_dummy_experiences(dummy_env, batch_size)
        buffer = ReplayBuffer()
        buffer.append_all(experiences)
        m_iqn.train_offline(buffer, total_iterations=5)

    def test_compute_eval_action(self):
        dummy_env = E.DummyDiscreteImg()
        m_iqn = A.MunchausenIQN(dummy_env)

        state = dummy_env.reset()
        state = np.float32(state)
        action = m_iqn.compute_eval_action(state)

        assert action.shape == (1, )

    def test_parameter_range(self):
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(gamma=1.1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(gamma=-0.1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(batch_size=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(replay_buffer_size=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(learner_update_frequency=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(max_explore_steps=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(learning_rate=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(initial_epsilon=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(final_epsilon=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(test_epsilon=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(K=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(N=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(N_prime=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(kappa=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(embedding_dim=-1)
        with pytest.raises(ValueError):
            A.MunchausenIQNConfig(clipping_value=100)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "./")
    from testing_utils import generate_dummy_experiences
    pytest.main()
else:
    from .testing_utils import generate_dummy_experiences
