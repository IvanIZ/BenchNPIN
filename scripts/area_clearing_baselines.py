"""
An example script for training and evaluating baselines for ship ice navigation
Uncomment the code blocks to train/evaluate each baseline algorithms
"""
import argparse

from benchnpin.baselines.area_clearing.ppo.policy import AreaClearingPPO
from benchnpin.baselines.area_clearing.sac.policy import AreaClearingSAC
from benchnpin.baselines.area_clearing.planning_based.policy import PlanningBasedPolicy
from benchnpin.baselines.area_clearing.sam.policy import AreaClearingSAM

from benchnpin.common.metrics.base_metric import BaseMetric

from benchnpin.common.utils.utils import DotDict
from os.path import dirname

import os

import pickle

def main(cfg, job_id):

    if cfg.train.train_mode:
        if cfg.train.resume_training:
            model_name = cfg.train.job_id_to_resume
        else:
            model_name = f'{cfg.train.job_name}_{job_id}'

        if cfg.train.job_type == 'sam':
            # ========================= Spatial Action Map Policy =========================
            sam_policy = AreaClearingSAM(model_name=model_name, cfg=cfg)
            sam_policy.train(job_id)

        elif cfg.train.job_type == 'ppo':
            # ================================ PPO Policy =================================    
            ppo_policy = AreaClearingPPO(model_name=model_name, cfg=cfg)
            ppo_policy.train(total_timesteps=cfg.train.total_timesteps, checkpoint_freq=cfg.train.checkpoint_freq, from_model_eps=cfg.train.from_model_eps)

        elif cfg.train.job_type == 'sac':
            # ================================ SAC Policy =================================
            sac_policy = AreaClearingSAC(model_name=model_name, cfg=cfg)
            sac_policy.train(total_timesteps=cfg.train.total_timesteps, checkpoint_freq=cfg.train.checkpoint_freq, from_model_eps=cfg.train.from_model_eps)

    if cfg.evaluate.eval_mode:
        benchmark_results = []
        num_eps = cfg.evaluate.num_eps
        model_path = cfg.evaluate.model_path
        for policy_type, model_name in zip(cfg.evaluate.policy_types, cfg.evaluate.model_names):
            if policy_type == 'sam':
                # ========================= Spatial Action Map Policy =========================
                sam_policy = AreaClearingSAM(model_name=model_name, model_path=model_path, cfg=cfg)
                benchmark_results.append(sam_policy.evaluate(num_eps=num_eps))

            elif policy_type == 'ppo':
                # ================================ PPO Policy =================================    
                ppo_policy = AreaClearingPPO(model_name=model_name, model_path=model_path, cfg=cfg)
                benchmark_results.append(ppo_policy.evaluate(num_eps=num_eps))

            elif policy_type == 'sac':
                # ================================ SAC Policy =================================
                sac_policy = AreaClearingSAC(model_name=model_name, model_path=model_path, cfg=cfg)
                benchmark_results.append(sac_policy.evaluate(num_eps=num_eps))

    BaseMetric.plot_algs_scores(benchmark_results, save_fig_dir='./', plot_success=True)

    # save eval results to disk
    pickle_dict = {
        'benchmark_results': benchmark_results
    }
    with open('ac_gtsp_benchmark_results.pkl', 'wb') as f:
        pickle.dump(pickle_dict, f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Train and evaluate baselines for area clearing task'
    )

    parser.add_argument(
        '--config_file',
        type=str,
        help='path to the config file',
        default=None
    )

    parser.add_argument(
        '--job_id',
        type=str,
        help='slurm job id',
        default=None
    )

    job_id = parser.parse_args().job_id

    if parser.parse_args().config_file is not None:
        cfg = DotDict.load_from_file(parser.parse_args().config_file)

    else:
        # High level configuration for the box delivery task
        cfg={
            'env': 'clear_env', # 'clear_env_small', 'clear_env', walled_env', 'walled_env_with_columns'
            'num_obstacles': 10,
            'render': {
                'log_obs': False, # log occupancy observations
                'show': True, # show the environment
            },
            'agent': {
                # Options: 'position', 'heading', 'velocity'
                'action_type': 'heading', # Use for PPO and SAC
                # 'action_type': 'position', # Used by default for SAM
                # action_type: 'velocity', # Use for GTSP
            },
            'train': {
                'train_mode': False,
                'job_type': 'sam', # 'sam', 'ppo', 'sac'
                'job_name': 'SAM',
                'from_model_eps': None,
            },
            'evaluate': {
                'eval_mode': True,
                'num_eps': 2,
                'policy_types': ['sam', 'ppo', 'sac'], # list of policy types to evaluate
                'model_names': ['clear_env_sam', 'ppo_model', 'sac_model'], # list of model names to evaluate
                'model_path': 'models/area_clearing', # list of model names to evaluate
                'obs_configs': [None], # list of obstacle configurations to evaluate
            }
        }

        cfg = DotDict.to_dot_dict(cfg)

    main(cfg, job_id)
    