import os

from clients.llm.base import LLMProvider
from clients.llm.bedrock_provider import BedrockLLMProvider
from clients.llm.gemini_provider import GeminiLLMProvider
from clients.llm.litellm_provider import LiteLLMProvider
from clients.llm.openai_provider import OpenAILLMProvider


def create_model_provider() -> LLMProvider:
    provider = os.getenv("AI_PROVIDER", "bedrock").lower()
    model_id = os.getenv("MODEL_ID")
    temperature = float(os.getenv("MODEL_TEMPERATURE", "0.3"))

    if provider == "gemini":
        return GeminiLLMProvider(
            api_key=os.getenv("GEMINI_API_KEY"),
            model_id=model_id or "gemini-flash-latest",
            temperature=temperature,
        )

    if provider == "litellm":
        return LiteLLMProvider(
            model_id=model_id or "gemini/gemini-2.5-flash",
            temperature=temperature,
        )

    if provider == "openai":
        return OpenAILLMProvider(
            model_id=model_id or "gpt-4o-mini",
            temperature=temperature,
        )

    if provider == "bedrock":
        return BedrockLLMProvider()

    raise ValueError(f"Unsupported AI_PROVIDER: {provider}")


def create_model():
    return create_model_provider().create_model()
