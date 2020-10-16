import warnings

import nnabla as nn
from nnabla.ext_utils import get_extension_context

from nnabla_rl.logger import logger

_gpu_id = -1


def run_on_gpu(cuda_device_id=0):
    global _gpu_id
    logger.info(
        'nnabla_rl will run the algorithm on gpu: {}'.format(cuda_device_id))
    _gpu_id = cuda_device_id


def run_on_cpu():
    global _gpu_id
    logger.info('nnabla_rl will run the algorithm on cpu')
    _gpu_id = -1


def _set_nnabla_context():
    global _gpu_id
    if _gpu_id < 0:
        _set_cpu_context()  # Set CPU as a default context.
        return
    try:
        # Run on CUDA
        _set_gpu_context(gpu_id=_gpu_id)
    except ModuleNotFoundError:
        warnings.warn('Could not set CUDA context and cuDNN context. \
                       Use CPU context intead', RuntimeWarning)
        _set_cpu_context()


def _set_gpu_context(gpu_id):
    ctx = get_extension_context('cudnn', device_id=gpu_id)
    nn.set_default_context(ctx)  # Set CUDA as a default context.


def _set_cpu_context():
    ctx = get_extension_context('cpu')
    nn.set_default_context(ctx)
