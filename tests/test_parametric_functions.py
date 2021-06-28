# Copyright 2021 Sony Group Corporation.
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

import numpy as np
import pytest

import nnabla as nn
import nnabla.functions as NF
import nnabla_rl.parametric_functions as RPF


class TestFunctions(object):
    def setup_method(self, method):
        nn.clear_parameters()

    def test_noisy_net_forward(self):
        nn.seed(0)
        x = nn.Variable.from_numpy_array(np.random.normal(size=(5, 5)))
        with nn.parameter_scope('noisy1'):
            y1 = RPF.noisy_net(x, n_outmap=10, seed=1)
            y1_params = nn.get_parameters()
        assert y1.shape == (5, 10)

        nn.seed(0)
        with nn.parameter_scope('noisy2'):
            y2 = RPF.noisy_net(x, n_outmap=10, seed=1)
            y2_params = nn.get_parameters()
        assert y1.shape == y2.shape
        assert y1_params.keys() == y2_params.keys()

        for param_name in ['W', 'noisy_W', 'b', 'noisy_b']:
            assert param_name in y1_params.keys()
        nn.forward_all([y1, y2])

        for y1_param, y2_param in zip(y1_params.values(), y2_params.values()):
            assert np.allclose(y1_param.d, y2_param.d)
        assert np.allclose(y1.d, y2.d)

    def test_noisy_net_rng(self):
        rng = np.random.RandomState(seed=0)
        x = nn.Variable.from_numpy_array(np.random.normal(size=(5, 5)))
        with nn.parameter_scope('noisy1'):
            y1 = RPF.noisy_net(x, n_outmap=10, seed=1, rng=rng)
            y1_params = nn.get_parameters()
        assert y1.shape == (5, 10)

        rng = np.random.RandomState(seed=0)
        with nn.parameter_scope('noisy2'):
            y2 = RPF.noisy_net(x, n_outmap=10, seed=1, rng=rng)
            y2_params = nn.get_parameters()
        assert y1.shape == y2.shape
        assert y1_params.keys() == y2_params.keys()

        for param_name in ['W', 'noisy_W', 'b', 'noisy_b']:
            assert param_name in y1_params.keys()
        nn.forward_all([y1, y2])

        for y1_param, y2_param in zip(y1_params.values(), y2_params.values()):
            assert np.allclose(y1_param.d, y2_param.d)
        assert np.allclose(y1.d, y2.d)

    def test_noisy_net_backward(self):
        nn.seed(0)
        x = nn.Variable.from_numpy_array(np.random.normal(size=(5, 5)))
        with nn.parameter_scope('noisy1'):
            y1 = RPF.noisy_net(x, n_outmap=10, seed=1)
            y1_params = nn.get_parameters()
        assert y1.shape == (5, 10)

        nn.seed(0)
        with nn.parameter_scope('noisy2'):
            y2 = RPF.noisy_net(x, n_outmap=10, seed=1)
            y2_params = nn.get_parameters()
        assert y1.shape == y2.shape
        for y1_param, y2_param in zip(y1_params.values(), y2_params.values()):
            y1_param.grad.zero()
            y2_param.grad.zero()

        loss = NF.sum((y1 - 1.0) ** 2 + (y2 - 5.0) ** 2)

        loss.forward()
        loss.backward()

        for y1_param, y2_param in zip(y1_params.values(), y2_params.values()):
            assert not np.allclose(y1_param.g, 0)
            assert not np.allclose(y2_param.g, 0)
            assert not np.allclose(y1_param.g, y2_param.g)

    def test_noisy_net_base_axis(self):
        x = nn.Variable.from_numpy_array(np.random.normal(size=(5, 5, 5)))
        with nn.parameter_scope('noisy1'):
            y1 = RPF.noisy_net(x, n_outmap=10, seed=1, base_axis=2)
        assert y1.shape == (5, 5, 10)

    def test_noisy_net_without_deterministic_bias(self):
        x = nn.Variable.from_numpy_array(np.random.normal(size=(5, 5)))
        with nn.parameter_scope('noisy1'):
            y1 = RPF.noisy_net(x, n_outmap=10, seed=1, with_bias=False)
            params = nn.get_parameters()

        assert y1.shape == (5, 10)
        assert 'b' not in params.keys()
        assert 'noisy_b' in params.keys()

    def test_noisy_net_without_noisy_bias(self):
        x = nn.Variable.from_numpy_array(np.random.normal(size=(5, 5)))
        with nn.parameter_scope('noisy1'):
            y1 = RPF.noisy_net(x, n_outmap=10, seed=1, with_noisy_bias=False)
            params = nn.get_parameters()
        assert y1.shape == (5, 10)
        assert 'b' in params.keys()
        assert 'noisy_b' not in params.keys()

    def test_noisy_net_without_bias(self):
        x = nn.Variable.from_numpy_array(np.random.normal(size=(5, 5)))
        with nn.parameter_scope('noisy1'):
            y1 = RPF.noisy_net(x, n_outmap=10, seed=1, with_bias=False, with_noisy_bias=False)
            params = nn.get_parameters()
        assert y1.shape == (5, 10)
        assert 'b' not in params.keys()
        assert 'noisy_b' not in params.keys()


if __name__ == "__main__":
    pytest.main()
