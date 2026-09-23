from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from backend.services.llm.base import (
    BaseLLMProvider,
    LLMProviderConfigurationError,
    LLMProviderResponseError,
    LLMResponse,
    LLMUsage,
)


class OpenAIProvider(
    BaseLLMProvider
):

    provider_name = "openai"

    BASE_URL = (
        "https://api.openai.com/v1"
    )

    DEFAULT_MODEL = (
        "gpt-4o-mini"
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
    ):

        self.api_key = (
            api_key or ""
        ).strip()

        self.default_model = (
            default_model
            or self.DEFAULT_MODEL
        )

    def is_configured(self) -> bool:

        return bool(
            self.api_key
        )

    def _headers(self):

        if not self.api_key:

            raise LLMProviderConfigurationError(
                "OpenAI API key is not configured."
            )

        return {
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
            "Content-Type": (
                "application/json"
            ),
        }

    async def _completion(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool = False,
    ) -> LLMResponse:

        selected_model = (
            model
            or self.default_model
        )

        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:

            payload["response_format"] = {
                "type": "json_object"
            }

        async with httpx.AsyncClient(
            timeout=120.0
        ) as client:

            response = await client.post(
                (
                    f"{self.BASE_URL}"
                    "/chat/completions"
                ),
                headers=self._headers(),
                json=payload,
            )

        if response.is_error:

            raise LLMProviderResponseError(
                (
                    "OpenAI request failed: "
                    f"{response.status_code} "
                    f"{response.text[:1000]}"
                )
            )

        data = response.json()

        try:

            content = (
                data["choices"][0]["message"]
                .get("content", "")
            )

        except (
            KeyError,
            IndexError,
            TypeError,
        ) as exc:

            raise LLMProviderResponseError(
                "OpenAI returned an invalid response."
            ) from exc

        usage_data = (
            data.get("usage")
            or {}
        )

        usage = LLMUsage(
            input_tokens=int(
                usage_data.get(
                    "prompt_tokens",
                    0,
                )
            ),
            output_tokens=int(
                usage_data.get(
                    "completion_tokens",
                    0,
                )
            ),
            total_tokens=int(
                usage_data.get(
                    "total_tokens",
                    0,
                )
            ),
        )

        return LLMResponse(
            content=content,
            usage=usage,
            provider=self.provider_name,
            model=selected_model,
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:

        return await self._completion(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:

        response = await self._completion(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )

        try:

            response.parsed_json = json.loads(
                response.content
            )

        except json.JSONDecodeError as exc:

            raise LLMProviderResponseError(
                "OpenAI returned invalid JSON."
            ) from exc

        return response

    def get_provider_info(
        self,
    ) -> Dict[str, Any]:

        return {
            "provider": self.provider_name,
            "configured": self.is_configured(),
            "default_model": self.default_model,
        }