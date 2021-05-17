# Copyright 2020,2021 Sony Corporation.
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

from typing import Iterable, List, Tuple, TypeVar, Union

import numpy as np

import nnabla as nn
from nnabla_rl.typing import TupledData

T = TypeVar('T')


def add_axis_if_single_dim(data):
    if data.ndim == 1:
        return np.expand_dims(data, axis=-1)
    else:
        return data


def marshal_experiences(experiences: Iterable[TupledData]) -> TupledData:
    '''Marshall experiences. This function concatenates each of the elements in the given experience and
    return it as a tuple. Note that if the given experience has a tuple, this function be applied recursively.

    Example:
        >>> import numpy as np
        >>> from nnabla_rl.utils.data import marshall_experiences
        >>> experiences = tuple((np.random.randn(1, ), np.random.randn(2, )) for _ in range(10))
        >>> marshaled_experience = marshall_experiences(experiences)
        >>> marshaled_experience[0].shape
        (10, 1)
        >>> marshaled_experience[1].shape
        (10, 2)
        >>> tupled_experiences = tuple(((np.random.randn(1, ), np.random.randn(2, )), np.random.randn(3, )) \
            for _ in range(10))
        >>> marshaled_tupled_experience = marshall_experiences(tupled_experiences)
        >>> type(tupled_experiences[0])
        <class 'tuple'>
        >>> marshaled_tupled_experience[0][0].shape
        (10, 1)
        >>> marshaled_tupled_experience[0][1].shape
        (10, 2)
        >>> marshaled_tupled_experience[1].shape
        (10, 3)

    Args:
        experiences (Iterable[TupledData]): iterable object of experience
    Returns:
        TupledData: marshaled experiences
    '''
    unzipped_experiences = unzip(experiences)
    marshaled_experiences = []
    for data in unzipped_experiences:
        if isinstance(data[0], tuple):
            marshaled_experiences.append(marshal_experiences(data))
        else:
            marshaled_experiences.append(add_axis_if_single_dim(np.asarray(data)))
    return tuple(marshaled_experiences)


def unzip(zipped_data):
    return list(zip(*zipped_data))


def is_array_like(x):
    return hasattr(x, "__len__")


def convert_to_list_if_not_list(value: Union[Iterable[T], T]) -> List[T]:
    if isinstance(value, Iterable):
        return list(value)
    else:
        return [value]


def set_data_to_variable(variable: Union[nn.Variable, Tuple[nn.Variable, ...]],
                         data: Union[float, np.ndarray, Tuple[np.ndarray, ...]]) -> None:
    '''Set data to variable

    Args:
        variable (Union[nn.Variable, Tuple[nn.Variable, ...]]): variable
        data (Union[float, np.ndarray, Tuple[np.ndarray, ...]]): data set to variable.d
    '''
    if isinstance(data, tuple) and isinstance(variable, tuple):
        assert len(variable) == len(data)
        for v, d in zip(variable, data):
            v.d = d
    elif isinstance(data, np.ndarray) and isinstance(variable, nn.Variable):
        variable.d = data
    elif isinstance(data, float) and isinstance(variable, nn.Variable):
        variable.d = data
    else:
        raise ValueError


def add_batch_dimension(data: Union[np.ndarray, Tuple[np.ndarray, ...]]) -> Union[np.ndarray, Tuple[np.ndarray, ...]]:
    '''Apply np.expand_dims to data. If the data is tuple, this function apply np.expand_dims to each elements of data.

    Args:
        data (Union[np.ndarray, Tuple[np.ndarray, ...]]): data
    Returns:
        Union[np.ndarray, Tuple[np.ndarray, ...]]: expanded data
    '''
    if isinstance(data, np.ndarray):
        return np.expand_dims(data, axis=0)
    else:
        return tuple(np.expand_dims(d, axis=0) for d in data)


class RingBuffer(object):
    def __init__(self, maxlen):
        # Do NOT replace this list with collections.deque.
        # deque is too slow when randomly accessed to sample data for creating batch
        self._buffer = [None for _ in range(maxlen)]
        self._maxlen = maxlen
        self._head = 0
        self._length = 0

    def __len__(self):
        return self._length

    def __getitem__(self, index):
        if index < 0 or index >= len(self):
            raise KeyError
        return self._buffer[(self._head + index) % self._maxlen]

    def append(self, data):
        self.append_with_removed_item_check(data)

    def append_with_removed_item_check(self, data):
        if self._length < self._maxlen:
            self._length += 1
        elif self._length == self._maxlen:
            self._head = (self._head + 1) % self._maxlen
        else:
            raise IndexError
        index = (self._head + self._length - 1) % self._maxlen
        removed = self._buffer[index]
        self._buffer[index] = data
        return removed
