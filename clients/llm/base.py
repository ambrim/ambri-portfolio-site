from abc import ABC, abstractmethod

from strands.models import Model


class LLMProvider(ABC):
    @abstractmethod
    def create_model(self) -> Model:
        raise NotImplementedError
