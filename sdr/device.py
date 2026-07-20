from abc import ABC, abstractmethod

import numpy as np
from numpy.typing import NDArray


ComplexArray = NDArray[np.complex64]


class SDRDevice(ABC):
    """
    Abstract interface for all SDR input devices.
    """

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_running(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def read_samples(
        self,
        num_samples: int,
    ) -> ComplexArray:
        raise NotImplementedError

    @abstractmethod
    def sample_rate(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def center_frequency(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def set_center_frequency(
        self,
        frequency_hz: float,
    ) -> None:
        raise NotImplementedError
