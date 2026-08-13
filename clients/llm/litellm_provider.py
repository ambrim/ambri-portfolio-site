from clients.llm.base import LLMProvider
from strands.models import Model


class LiteLLMProvider(LLMProvider):
    def __init__(
        self,
        model_id: str = "gemini/gemini-2.5-flash",
        temperature: float = 0.3,
    ):
        self.model_id = model_id
        self.temperature = temperature

    def create_model(self) -> Model:
        from strands.models.litellm import LiteLLMModel

        return LiteLLMModel(
            model_id=self.model_id,
            params={"temperature": self.temperature},
        )
