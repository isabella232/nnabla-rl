import nnabla as nn
import nnabla.functions as F
import nnabla.parametric_functions as PF

from nnabla_rl.models.perturbator import Perturbator


class BCQPerturbator(Perturbator):
    """
    Perturbator model proposed by S. Fujimoto in BCQ paper for mujoco environment.
    See: https://arxiv.org/abs/1812.02900
    """

    def __init__(self, scope_name, state_dim, action_dim, max_action_value):
        super(BCQPerturbator, self).__init__(scope_name)
        self._state_dim = state_dim
        self._action_dim = action_dim
        self._max_action_value = max_action_value

    def generate_noise(self, s, a, phi):
        assert s.shape[1] == self._state_dim

        with nn.parameter_scope(self.scope_name):
            h = F.concatenate(s, a)
            h = PF.affine(h, n_outmaps=400, name="linear1")
            h = F.relu(x=h)
            h = PF.affine(h, n_outmaps=300, name="linear2")
            h = F.relu(x=h)
            h = PF.affine(h, n_outmaps=self._action_dim, name="linear3")
        return F.tanh(h) * self._max_action_value * phi
