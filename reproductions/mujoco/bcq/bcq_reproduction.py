import argparse

import gym

import numpy as np

import d4rl

import nnabla_rl
import nnabla_rl.algorithms as A
import nnabla_rl.hooks as H
import nnabla_rl.writers as W
import nnabla_rl.utils.context as context
from nnabla_rl.utils.evaluator import EpisodicEvaluator
from nnabla_rl.utils.reproductions import build_mujoco_env, d4rl_dataset_to_buffer
from nnabla_rl.hook import as_hook
from nnabla_rl.logger import logger
from nnabla_rl.utils import serializers
from nnabla_rl.replay_buffer import ReplayBuffer


def run_training(args):
    nnabla_rl.run_on_gpu(cuda_device_id=0)

    outdir = '{}_results'.format(args.env)

    eval_env = build_mujoco_env(
        args.env, test=True, seed=100)
    evaluator = EpisodicEvaluator(run_per_evaluation=10)
    evaluation_hook = H.EvaluationHook(eval_env,
                                       evaluator,
                                       timing=5000,
                                       writer=W.FileWriter(outdir=outdir,
                                                           file_prefix='evaluation_result'))

    save_snapshot_hook = H.SaveSnapshotHook(outdir, timing=5000)
    iteration_num_hook = H.IterationNumHook(timing=100)

    train_env = gym.make(args.env)
    train_dataset = train_env.get_dataset()
    buffer = d4rl_dataset_to_buffer(train_dataset)
    if args.snapshot_dir is None:
        bcq = A.BCQ(train_env)
    else:
        bcq = serializers.load_snapshot(args.snapshot_dir)
    hooks = [iteration_num_hook, save_snapshot_hook, evaluation_hook]
    bcq.set_hooks(hooks)

    bcq.train_offline(buffer, total_iterations=1000000)

    eval_env.close()
    train_env.close()


def run_showcase(args):
    nnabla_rl.run_on_gpu(cuda_device_id=0)

    if args.snapshot_dir is None:
        raise ValueError(
            'Please specify the snapshot dir for showcasing')
    bcq = serializers.load_snapshot(args.snapshot_dir)
    if not isinstance(bcq, A.BCQ):
        raise ValueError('Loaded snapshot is not trained with BCQ!')

    eval_env = build_mujoco_env(
        args.env, test=True, seed=200, render=True)
    evaluator = EpisodicEvaluator()
    evaluator(bcq, eval_env)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=str, default='ant-expert-v0')
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--showcase', action='store_true')
    parser.add_argument('--snapshot-dir', type=str, default=None)

    args = parser.parse_args()

    if args.showcase:
        run_showcase(args)
    else:
        run_training(args)


if __name__ == '__main__':
    main()
