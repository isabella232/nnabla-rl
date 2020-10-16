import gym

import numpy as np
import argparse

import nnabla_rl
import nnabla_rl.algorithms as A
import nnabla_rl.hooks as H
import nnabla_rl.replay_buffers as RB
from nnabla_rl.utils.evaluator import TimestepEvaluator, EpisodicEvaluator
from nnabla_rl.utils.reproductions import build_atari_env
from nnabla_rl.utils import serializers
from nnabla_rl.writers import FileWriter
from nnabla_rl.hook import as_hook
from nnabla_rl.logger import logger


@as_hook(timing=100)
def print_iteration_number(algorithm):
    print('Current iteration: {}'.format(algorithm.iteration_num))


def memory_efficient_buffer_builder(capacity):
    return RB.MemoryEfficientAtariBuffer(capacity=capacity)


def run_training(args):
    nnabla_rl.run_on_gpu(cuda_device_id=0)

    eval_env = build_atari_env(
        args.env, test=True, seed=100, render=args.render)

    outdir = '{}_results'.format(args.env)
    writer = FileWriter(outdir, "evaluation_result")
    evaluator = TimestepEvaluator(num_timesteps=125000)
    evaluation_hook = H.EvaluationHook(eval_env, evaluator,
                                       timing=250000, writer=writer)

    save_snapshot_hook = H.SaveSnapshotHook(
        outdir, timing=250000)

    train_env = build_atari_env(args.env)

    params = A.DQNParam()
    dqn = A.DQN(train_env,
                params=params,
                replay_buffer_builder=memory_efficient_buffer_builder)
    dqn.set_hooks(hooks=[print_iteration_number,
                         save_snapshot_hook,
                         evaluation_hook])

    dqn.train(train_env, total_iterations=50000000)

    eval_env.close()
    train_env.close()


def run_showcase(args):
    nnabla_rl.run_on_gpu(cuda_device_id=0)

    if args.snapshot_dir is None:
        raise ValueError(
            'Please specify the snapshot dir for showcasing')
    dqn = serializers.load_snapshot(args.snapshot_dir)
    if not isinstance(dqn, A.DQN):
        raise ValueError('Loaded snapshot is not trained with DQN!')
    dqn.update_algorithm_params(**{'test_epsilon': 0.05})

    eval_env = build_atari_env(
        args.env, test=True, seed=200, render=False)
    evaluator = EpisodicEvaluator(run_per_evaluation=30)
    returns = evaluator(dqn, eval_env)
    mean = np.mean(returns)
    std_dev = np.std(returns)
    median = np.median(returns)
    logger.info('Evaluation results. mean: {} +/- std: {}, median: {}'.format(
        mean, std_dev, median))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=str,
                        default='BreakoutNoFrameskip-v4')
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
