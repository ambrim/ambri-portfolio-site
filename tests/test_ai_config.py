import os
import unittest
from unittest.mock import patch

from clients.llm.bedrock_provider import BedrockLLMProvider
from clients.llm.gemini_provider import GeminiLLMProvider
from clients.llm.litellm_provider import LiteLLMProvider
from clients.llm.openai_provider import OpenAILLMProvider
from utils.ai_config import create_model_provider


class AIConfigTests(unittest.TestCase):
    def test_gemini_provider_selected_from_env(self):
        with patch.dict(
            os.environ,
            {
                "AI_PROVIDER": "gemini",
                "MODEL_ID": "gemini-test",
                "GEMINI_API_KEY": "key",
                "MODEL_TEMPERATURE": "0.1",
            },
            clear=False,
        ):
            provider = create_model_provider()

        self.assertIsInstance(provider, GeminiLLMProvider)
        self.assertEqual(provider.model_id, "gemini-test")
        self.assertEqual(provider.api_key, "key")
        self.assertEqual(provider.temperature, 0.1)

    def test_litellm_provider_selected_from_env(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "litellm", "MODEL_ID": "gemini/foo"}, clear=False):
            provider = create_model_provider()

        self.assertIsInstance(provider, LiteLLMProvider)
        self.assertEqual(provider.model_id, "gemini/foo")

    def test_openai_provider_selected_from_env(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "openai", "MODEL_ID": "gpt-test"}, clear=False):
            provider = create_model_provider()

        self.assertIsInstance(provider, OpenAILLMProvider)
        self.assertEqual(provider.model_id, "gpt-test")

    def test_bedrock_provider_is_default(self):
        with patch.dict(os.environ, {}, clear=True):
            provider = create_model_provider()

        self.assertIsInstance(provider, BedrockLLMProvider)


if __name__ == "__main__":
    unittest.main()
