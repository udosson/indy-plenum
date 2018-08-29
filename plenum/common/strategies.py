from abc import ABC, abstractmethod
from collections import defaultdict
from statistics import median_low, median, median_high
from typing import List

from plenum.common.moving_average import EMAEventFrequencyEstimator


class AverageStrategyBase(ABC):
    @staticmethod
    def get_avg(metrics: List):
        raise NotImplementedError()


class MedianLowStrategy(AverageStrategyBase):
    @staticmethod
    def get_avg(metrics: List):
        return median_low(metrics)


class MedianMediumStrategy(AverageStrategyBase):
    @staticmethod
    def get_avg(metrics: List):
        return median(metrics)


class MedianHighStrategy(AverageStrategyBase):
    @staticmethod
    def get_avg(metrics: List):
        return median_high(metrics)


class MonitorStrategy(ABC):
    @abstractmethod
    def add_instance(self):
        pass

    @abstractmethod
    def remove_instance(self):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def update_time(self, timestamp: float):
        pass

    @abstractmethod
    def request_received(self, id: str):
        pass

    @abstractmethod
    def request_ordered(self, id: str, inst_id: int):
        pass

    @abstractmethod
    def is_master_degraded(self) -> bool:
        return False


class AccumulatingMonitorStrategy(MonitorStrategy):
    def __init__(self, start_time: float, instances: int, txn_delta_k: int, timeout: float,
                 input_rate_reaction_half_time: float):
        self._instances = instances
        self._txn_delta_k = txn_delta_k
        self._timeout = timeout
        self._ordered = defaultdict(lambda: 0)
        self._timestamp = start_time
        self._alert_timestamp = None
        self._input_txn_rate = EMAEventFrequencyEstimator(start_time, input_rate_reaction_half_time)

    def add_instance(self):
        self._instances += 1

    def remove_instance(self):
        self._instances -= 1

    def reset(self):
        self._alert_timestamp = None
        self._ordered.clear()

    def update_time(self, timestamp: float):
        self._timestamp = timestamp
        self._input_txn_rate.update_time(timestamp)
        if not self._is_degraded():
            self._alert_timestamp = None
        elif not self._alert_timestamp:
            self._alert_timestamp = self._timestamp

    def request_received(self, id: str):
        self._input_txn_rate.add_events(1)

    def request_ordered(self, id: str, inst_id: int):
        self._ordered[inst_id] += 1

    def is_master_degraded(self) -> bool:
        if self._alert_timestamp is None:
            return False
        return self._timestamp - self._alert_timestamp > self._timeout

    def _is_degraded(self):
        if self._instances < 2:
            return False
        master_ordered = self._ordered[0]
        max_ordered = max(self._ordered[i] for i in range(1, self._instances))
        return (max_ordered - master_ordered) > self._txn_delta_k * self._input_txn_rate.value
