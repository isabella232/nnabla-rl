import argparse

import gym

import numpy as np

import nnabla_rl
import nnabla_rl.algorithms as A
import nnabla_rl.hooks as H
import nnabla_rl.writers as W
import nnabla_rl.utils.context as context
from nnabla_rl.utils.evaluator import EpisodicEvaluator
from nnabla_rl.utils.reproductions import build_mujoco_env
from nnabla_rl.hook import as_hook
from nnabla_rl.logger import logger
from nnabla_rl.utils import serializers


def select_start_timesteps(env_name):
    if env_name in ['Ant-v2', 'HalfCheetah-v2']:
        timesteps = 10000
    else:
        timesteps = 1000
    print(f'Selected start timesteps: {timesteps}')
    return timesteps


def select_total_iterations(env_name):
    if env_name in ['Hopper-v2', 'Walker2d-v2']:
        total_iterations = 1000000
    elif env_name in ['Humanoid-v2']:
        total_iterations = 10000000
    else:
        total_iterations = 3000000
    print(f'Selected total iterations: {total_iterations}')
    return total_iterations


def select_reward_scalar(env_name):
    if env_name in ['Humanoid-v2']:
        scalar = 20.0
    else:
        scalar = 5.0
    print(f'Selected reward scalar: {scalar}')
    return scalar


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

    train_env = build_mujoco_env(args.env, seed=1, render=args.render)
    if args.snapshot_dir is None:
        timesteps = select_start_timesteps(args.env)
        reward_scalar = select_reward_scalar(args.env)
        params = A.ICML2018SACParam(
            start_timesteps=timesteps, reward_scalar=reward_scalar)
        icml2018sac = A.ICML2018SAC(train_env, params=params)
    else:
        icml2018sac = serializers.load_snapshot(args.snapshot_dir)
    hooks = [iteration_num_hook, save_snapshot_hook, evaluation_hook]
    icml2018sac.set_hooks(hooks)

    total_iterations = select_total_iterations(args.env)
    icml2018sac.train_online(train_env, total_iterations=total_iterations)

    eval_env.close()
    train_env.close()


def run_showcase(args):
    nnabla_rl.run_on_gpu(cuda_device_id=0)

    if args.snapshot_dir is None:
        raise ValueError(
            'Please specify the snapshot dir for showcasing')
    icml2018sac = serializers.load_snapshot(args.snapshot_dir)
    if not isinstance(icml2018sac, A.ICML2018SAC):
        raise ValueError('Loaded snapshot is not trained with ICML2018SAC!')

    eval_env = build_mujoco_env(
        args.env, test=True, seed=200, render=True)
    evaluator = EpisodicEvaluator()
    evaluator(icml2018sac, eval_env)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=str, default='Ant-v2')
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
