from clients.llm.base import LLMProvider
from strands.models import Model


class BedrockLLMProvider(LLMProvider):
    def create_model(self) -> Model:
        from utils.aws_config import create_bedrock_model

        return create_bedrock_model()
