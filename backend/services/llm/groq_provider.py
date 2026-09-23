import json
import logging
import os
from typing import Any, Dict, List, Optional

from groq import AsyncGroq

from backend.services.llm.base import (
    BaseLLMProvider,
    LLMProviderConfigurationError,
    LLMProviderResponseError,
    LLMResponse,
    LLMUsage,
)


logger = logging.getLogger("smarthire.llm.groq")


DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


class GroqProvider(BaseLLMProvider):

    provider_name = "groq"

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        self.api_key = (
            api_key
            or os.getenv("GROQ_API_KEY")
        )

        self.default_model = (
            default_model
            or DEFAULT_GROQ_MODEL
        )

        self.client: Optional[AsyncGroq] = None

        if self.api_key:
            self.client = AsyncGroq(
                api_key=self.api_key
            )

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def is_configured(self) -> bool:
        return bool(
            self.api_key
            and self.client
        )

    # ========================================================
    # USAGE
    # ========================================================

    @staticmethod
    def _extract_usage(
        response: Any,
    ) -> LLMUsage:

        provider_usage = getattr(
            response,
            "usage",
            None,
        )

        if provider_usage is None:
            return LLMUsage()

        input_tokens = int(
            getattr(
                provider_usage,
                "prompt_tokens",
                0,
            )
            or 0
        )

        output_tokens = int(
            getattr(
                provider_usage,
                "completion_tokens",
                0,
            )
            or 0
        )

        total_tokens = int(
            getattr(
                provider_usage,
                "total_tokens",
                input_tokens + output_tokens,
            )
            or (
                input_tokens
                + output_tokens
            )
        )

        return LLMUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    # ========================================================
    # INTERNAL REQUEST
    # ========================================================

    async def _create_completion(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool = False,
    ) -> LLMResponse:

        if not self.is_configured():
            raise LLMProviderConfigurationError(
                "Groq provider is not configured. "
                "Please set GROQ_API_KEY."
            )

        selected_model = (
            model
            or self.default_model
        )

        try:

            kwargs: Dict[str, Any] = {
                "model": selected_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if json_mode:
                kwargs["response_format"] = {
                    "type": "json_object"
                }

            response = await self.client.chat.completions.create(
                **kwargs
            )

        except Exception as exc:

            logger.exception(
                "Groq request failed."
            )

            raise LLMProviderResponseError(
                "Groq request failed."
            ) from exc

        try:

            choices = getattr(
                response,
                "choices",
                None,
            )

            if not choices:
                raise ValueError(
                    "Groq returned no choices."
                )

            message = choices[0].message

            content = (
                getattr(
                    message,
                    "content",
                    None,
                )
                or ""
            ).strip()

        except Exception as exc:

            logger.exception(
                "Could not parse Groq response."
            )

            raise LLMProviderResponseError(
                "Could not parse Groq response."
            ) from exc

        usage = self._extract_usage(
            response
        )

        return LLMResponse(
            content=content,
            usage=usage,
            provider=self.provider_name,
            model=selected_model,
        )

    # ========================================================
    # TEXT GENERATION
    # ========================================================

    async def generate(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:

        return await self._create_completion(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=False,
        )

    # ========================================================
    # JSON GENERATION
    # ========================================================

    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:

        response = await self._create_completion(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )

        try:

            parsed = json.loads(
                response.content
            )

        except json.JSONDecodeError as exc:

            logger.error(
                "Groq returned invalid JSON."
            )

            raise LLMProviderResponseError(
                "Groq returned invalid JSON."
            ) from exc

        if not isinstance(
            parsed,
            dict,
        ):
            raise LLMProviderResponseError(
                "Groq JSON response must be an object."
            )

        response.parsed_json = parsed

        return response

    # ========================================================
    # PROVIDER INFO
    # ========================================================

    def get_provider_info(
        self,
    ) -> Dict[str, Any]:

        return {
            "provider": self.provider_name,
            "configured": self.is_configured(),
            "default_model": self.default_model,
        }