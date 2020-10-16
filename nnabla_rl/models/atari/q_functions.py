import nnabla as nn

import nnabla.functions as F
import nnabla.parametric_functions as PF

import numpy as np

import nnabla_rl.initializers as RI
import nnabla_rl.functions as RF
from nnabla_rl.models.q_function import QFunction


class DQNQFunction(QFunction):
    """
    Q function proposed by DeepMind in DQN paper for atari environment.
    See: https://deepmind.com/research/publications/human-level-control-through-deep-reinforcement-learning
    """

    def __init__(self, scope_name, state_shape, n_action):
        super(DQNQFunction, self).__init__(scope_name)
        dummy_state = nn.Variable((1, *state_shape))
        dummy_action = nn.Variable((1, 1))

        self._state_shape = state_shape
        self._n_action = n_action

    def _predict_q_values(self, s):
        """ Predict all q values of the given state
        """
        with nn.parameter_scope(self.scope_name):

            with nn.parameter_scope("conv1"):
                h = F.relu(PF.convolution(s, 32, (8, 8), stride=(4, 4),
                                          w_init=RI.HeNormal(s.shape[1],
                                                             32,
                                                             kernel=(8, 8))
                                          ))

            with nn.parameter_scope("conv2"):
                h = F.relu(PF.convolution(h, 64, (4, 4), stride=(2, 2),
                                          w_init=RI.HeNormal(h.shape[1],
                                                             64,
                                                             kernel=(4, 4))
                                          ))

            with nn.parameter_scope("conv3"):
                h = F.relu(PF.convolution(h, 64, (3, 3), stride=(1, 1),
                                          w_init=RI.HeNormal(h.shape[1],
                                                             64,
                                                             kernel=(3, 3))
                                          ))

            h = F.reshape(h, (-1, 3136))

            with nn.parameter_scope("affine1"):
                h = F.relu(PF.affine(h, 512,
                                     w_init=RI.HeNormal(h.shape[1], 512)
                                     ))

            with nn.parameter_scope("affine2"):
                h = PF.affine(h, self._n_action,
                              w_init=RI.HeNormal(h.shape[1], self._n_action)
                              )
        return h

    def q(self, s, a):
        batch_size = s.shape[0]

        q_values = self._predict_q_values(s)

        q_value = F.sum(q_values
                        * F.one_hot(F.reshape(a, (-1, 1), inplace=False),
                                    (q_values.shape[1],)),
                        axis=1, keepdims=True)  # get q value of a

        return q_value

    def maximum(self, s):
        q_values = self._predict_q_values(s)
        return F.max(q_values, axis=1, keepdims=True)

    def argmax(self, s):
        q_values = self._predict_q_values(s)
        return RF.argmax(q_values, axis=1)
