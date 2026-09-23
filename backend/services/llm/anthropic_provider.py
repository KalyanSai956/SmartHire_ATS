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


class AnthropicProvider(
    BaseLLMProvider
):

    provider_name = "anthropic"

    BASE_URL = (
        "https://api.anthropic.com/v1"
    )

    DEFAULT_MODEL = (
        "claude-3-5-haiku-latest"
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
                "Anthropic API key is not configured."
            )

        return {
            "x-api-key": self.api_key,
            "anthropic-version": (
                "2023-06-01"
            ),
            "Content-Type": (
                "application/json"
            ),
        }

    def _convert_messages(
        self,
        messages: List[Dict[str, str]],
    ):

        system_messages = []

        user_messages = []

        for message in messages:

            role = message.get(
                "role",
                "user",
            )

            content = message.get(
                "content",
                "",
            )

            if role == "system":

                system_messages.append(
                    content
                )

            else:

                anthropic_role = (
                    "assistant"
                    if role == "assistant"
                    else "user"
                )

                user_messages.append(
                    {
                        "role": anthropic_role,
                        "content": content,
                    }
                )

        return (
            system_messages,
            user_messages,
        )

    async def _completion(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:

        selected_model = (
            model
            or self.default_model
        )

        (
            system_messages,
            converted_messages,
        ) = self._convert_messages(
            messages
        )

        payload = {
            "model": selected_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": converted_messages,
        }

        if system_messages:

            payload["system"] = (
                "\n\n".join(
                    system_messages
                )
            )

        async with httpx.AsyncClient(
            timeout=120.0
        ) as client:

            response = await client.post(
                (
                    f"{self.BASE_URL}"
                    "/messages"
                ),
                headers=self._headers(),
                json=payload,
            )

        if response.is_error:

            raise LLMProviderResponseError(
                (
                    "Anthropic request failed: "
                    f"{response.status_code} "
                    f"{response.text[:1000]}"
                )
            )

        data = response.json()

        try:

            content = "".join(
                block.get(
                    "text",
                    "",
                )
                for block in data.get(
                    "content",
                    [],
                )
                if block.get(
                    "type"
                ) == "text"
            )

        except Exception as exc:

            raise LLMProviderResponseError(
                "Anthropic returned invalid content."
            ) from exc

        usage_data = (
            data.get("usage")
            or {}
        )

        input_tokens = int(
            usage_data.get(
                "input_tokens",
                0,
            )
        )

        output_tokens = int(
            usage_data.get(
                "output_tokens",
                0,
            )
        )

        return LLMResponse(
            content=content,
            usage=LLMUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=(
                    input_tokens
                    + output_tokens
                ),
            ),
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
        )

        try:

            response.parsed_json = json.loads(
                response.content
            )

        except json.JSONDecodeError as exc:

            raise LLMProviderResponseError(
                "Anthropic returned invalid JSON."
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