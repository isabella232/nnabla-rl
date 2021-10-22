#!/usr/bin/env bash
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

if [ $# -ne 3 ]; then
    echo "usage: $0 <gpu_id> <env> <flicker>"
    exit 1
fi

for seed in 1 10 100
do
    if [ $3 = "no-flicker" ];then
        python drqn_reproduction.py --gpu $1 --seed $seed --env $2 --save-dir ./
    fi
    if [ $3 = "flicker" ];then
        python drqn_reproduction.py --gpu $1 --seed $seed --env $2 --flicker --save-dir ./
    fi
done