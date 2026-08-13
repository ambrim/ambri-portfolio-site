from clients.llm.base import LLMProvider
from strands.models import Model


class OpenAILLMProvider(LLMProvider):
    def __init__(
        self,
        model_id: str = "gpt-4o-mini",
        temperature: float = 0.3,
    ):
        self.model_id = model_id
        self.temperature = temperature

    def create_model(self) -> Model:
        from strands.models.openai import OpenAIModel

        return OpenAIModel(
            model_id=self.model_id,
            params={"temperature": self.temperature},
        )
