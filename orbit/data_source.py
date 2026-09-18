from abc import ABC, abstractmethod


class DataSource(ABC):
    @abstractmethod
    def current_state(self):
        pass

    @abstractmethod
    def step(self):
        pass

    @abstractmethod
    def reset(self):
        pass