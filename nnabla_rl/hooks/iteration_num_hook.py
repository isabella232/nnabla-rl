# Copyright (c) 2021 Sony Group Corporation. All Rights Reserved.
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

from nnabla_rl.hook import Hook
from nnabla_rl.logger import logger


class IterationNumHook(Hook):
    '''
    Hook to print the iteration number periodically.
    This hook just prints the iteration number of training.

    Args:
        timing (int): Printing interval. Defaults to 1 iteration.
    '''

    def __init__(self, timing=1):
        super(IterationNumHook, self).__init__(timing=timing)

    def on_hook_called(self, algorithm):
        logger.info("current iteration: {}".format(algorithm.iteration_num))
