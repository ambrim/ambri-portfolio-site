from clients.llm.base import LLMProvider
from strands.models import Model


class GeminiLLMProvider(LLMProvider):
    def __init__(
        self,
        api_key: str | None,
        model_id: str = "gemini-flash-latest",
        temperature: float = 0.3,
    ):
        self.api_key = api_key
        self.model_id = model_id
        self.temperature = temperature

    def create_model(self) -> Model:
        from strands.models.gemini import GeminiModel

        return GeminiModel(
            client_args={"api_key": self.api_key},
            model_id=self.model_id,
            params={"temperature": self.temperature},
        )
