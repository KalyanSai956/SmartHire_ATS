import json
import logging
from typing import Any, Dict, List, Optional

from groq import AsyncGroq

from backend.core.config import GROQ_API_KEY

from backend.services.llm.base import (
    BaseLLMProvider,
    LLMProviderConfigurationError,
    LLMProviderResponseError,
)


logger = logging.getLogger("smarthire.llm.groq")

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


class GroqProvider(BaseLLMProvider):
    """
    Groq implementation of the SmartHire LLM interface.

    Uses the existing SmartHire configuration system.
    The API key is never exposed to the frontend.
    """

    provider_name = "groq"

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        # Prefer explicitly supplied key.
        # Otherwise use SmartHire's central configuration.
        self.api_key = api_key or GROQ_API_KEY

        self.default_model = (
            default_model
            or "openai/gpt-oss-120b"
        )

        self.client: Optional[AsyncGroq] = None

        if self.api_key:
            self.client = AsyncGroq(
                api_key=self.api_key
            )

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _require_client(self) -> AsyncGroq:
        if not self.api_key or not self.client:
            raise LLMProviderConfigurationError(
                "Groq API key is not configured."
            )

        return self.client

    def _resolve_model(
        self,
        model: Optional[str],
    ) -> str:
        return model or self.default_model

    async def generate(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:

        client = self._require_client()

        selected_model = self._resolve_model(model)

        try:
            response = await client.chat.completions.create(
                model=selected_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        except Exception as exc:
            logger.exception(
                "Groq generation failed."
            )

            raise LLMProviderResponseError(
                f"Groq generation failed: {exc}"
            ) from exc

        try:
            content = response.choices[0].message.content

        except (AttributeError, IndexError) as exc:
            raise LLMProviderResponseError(
                "Groq returned an invalid response."
            ) from exc

        if not content:
            raise LLMProviderResponseError(
                "Groq returned an empty response."
            )

        return content.strip()

    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> Dict[str, Any]:

        client = self._require_client()

        selected_model = self._resolve_model(model)

        try:
            response = await client.chat.completions.create(
                model=selected_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={
                    "type": "json_object"
                },
            )

        except Exception as exc:
            logger.exception(
                "Groq JSON generation failed."
            )

            raise LLMProviderResponseError(
                f"Groq JSON generation failed: {exc}"
            ) from exc

        try:
            content = response.choices[0].message.content

        except (AttributeError, IndexError) as exc:
            raise LLMProviderResponseError(
                "Groq returned an invalid JSON response."
            ) from exc

        if not content:
            raise LLMProviderResponseError(
                "Groq returned an empty JSON response."
            )

        try:
            parsed = json.loads(content)

        except json.JSONDecodeError as exc:
            logger.error(
                "Groq returned invalid JSON: %s",
                content,
            )

            raise LLMProviderResponseError(
                "Groq returned invalid JSON."
            ) from exc

        if not isinstance(parsed, dict):
            raise LLMProviderResponseError(
                "Groq JSON response must be an object."
            )

        return parsed

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "configured": self.is_configured(),
            "default_model": self.default_model,
        }