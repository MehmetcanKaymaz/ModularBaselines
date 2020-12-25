import time
from collections import deque
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Union

from stable_baselines3.common import logger
from stable_baselines3.common.utils import safe_mean, configure_logger

from modular_baselines.algorithms.callbacks import BaseAlgorithmCallback
from modular_baselines.collectors.callbacks import BaseCollectorCallback


class InitLogCallback(BaseAlgorithmCallback):
    """ Initialize a standard Stable-Baselines3 logger without tensorboard writer.
    At every training step, check if the the logging period matches with the
    iteration number. If so, record the basic information about the training and
    dump the logs.

    Args:
        log_interval (int): Log at every n steps.
        save_dir (str, optional): Path of the directory to save files if there
            any. Defaults to None.
    """

    def __init__(self, log_interval: int, save_dir: str = None):
        self.log_interval = log_interval
        logger.configure(folder=save_dir)

    def _on_training_start(self, *args) -> None:
        self.start_time = time.time()

    def _on_step(self, locals_) -> bool:
        if locals_["iteration"] % self.log_interval == 0:
            fps = int(locals_["num_timesteps"] /
                      (time.time() - self.start_time))
            logger.record("time/iterations",
                          locals_["iteration"],
                          exclude="tensorboard")
            logger.record("time/fps",
                          fps)
            logger.record("time/time_elapsed",
                          int(time.time() - self.start_time),
                          exclude="tensorboard")
            logger.record("time/total_timesteps",
                          locals_["num_timesteps"],
                          exclude="tensorboard")
            logger.dump(step=locals_["num_timesteps"])

    def _on_training_end(self, *args) -> None:
        pass


class LogRolloutCallback(BaseCollectorCallback):
    """ Accumulate the rewards and episode lengths of the experiences gathered
    by the collector. At the end of a rollout, record the average values. 
    """

    def __init__(self):
        super().__init__()
        self.reset_info()

    def reset_info(self):
        self.ep_info_buffer = deque(maxlen=100)
        self.ep_success_buffer = deque(maxlen=100)

    def _on_rollout_start(self, *args) -> None:
        pass

    def _on_rollout_step(self, locals_) -> None:
        dones = locals_["dones"]
        infos = locals_["infos"]

        if dones is None:
            dones = np.array([False] * len(infos))
        for idx, info in enumerate(infos):
            maybe_ep_info = info.get("episode")
            maybe_is_success = info.get("is_success")
            if maybe_ep_info is not None:
                self.ep_info_buffer.extend([maybe_ep_info])
            if maybe_is_success is not None and dones[idx]:
                self.ep_success_buffer.append(maybe_is_success)

    def _on_rollout_end(self, locals_) -> None:
        if len(self.ep_info_buffer) > 0 and len(self.ep_info_buffer[0]) > 0:
            logger.record_mean(
                "rollout/ep_rew_mean", safe_mean([ep_info["r"] for ep_info in self.ep_info_buffer]))
            logger.record_mean(
                "rollout/ep_len_mean", safe_mean([ep_info["l"] for ep_info in self.ep_info_buffer]))
        self.reset_info()
