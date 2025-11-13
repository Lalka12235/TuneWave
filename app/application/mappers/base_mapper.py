from abc import ABC, abstractmethod

class BaseMapper(ABC):
    @abstractmethod
    def to_response(self, model):
        pass