from abc import ABC, abstractmethod


class SDRDevice(ABC):
    @abstractmethod
    def read_samples(self, num_samples: int):
        pass

    @abstractmethod
    def sample_rate(self):
        pass