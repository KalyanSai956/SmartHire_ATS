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


class GoogleProvider(
    BaseLLMProvider
):

    provider_name = "google"

    BASE_URL = (
        "https://generativelanguage.googleapis.com/v1beta"
    )

    DEFAULT_MODEL = (
       "gemini-3.6-flash"
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

    def _convert_messages(
        self,
        messages: List[Dict[str, str]],
    ):

        contents = []

        system_instruction = None

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

                system_instruction = {
                    "parts": [
                        {
                            "text": content
                        }
                    ]
                }

                continue

            contents.append(
                {
                    "role": (
                        "model"
                        if role == "assistant"
                        else "user"
                    ),
                    "parts": [
                        {
                            "text": content
                        }
                    ],
                }
            )

        return (
            contents,
            system_instruction,
        )

    async def _completion(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool = False,
    ) -> LLMResponse:

        if not self.api_key:

            raise LLMProviderConfigurationError(
                "Google AI API key is not configured."
            )

        selected_model = (
            model
            or self.default_model
        )

        (
            contents,
            system_instruction,
        ) = self._convert_messages(
            messages
        )

        generation_config = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }

        if json_mode:

            generation_config[
                "responseMimeType"
            ] = "application/json"

        payload = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        if system_instruction:

            payload[
                "systemInstruction"
            ] = system_instruction

        url = (
            f"{self.BASE_URL}"
            f"/models/{selected_model}"
            f":generateContent"
        )

        async with httpx.AsyncClient(
            timeout=120.0
        ) as client:

            response = await client.post(
                url,
               headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": self.api_key,
},
                json=payload,
            )

        if response.is_error:

            raise LLMProviderResponseError(
                (
                    "Google AI request failed: "
                    f"{response.status_code} "
                    f"{response.text[:1000]}"
                )
            )

        data = response.json()

        try:

            parts = (
                data["candidates"][0]
                ["content"]
                ["parts"]
            )

            content = "".join(
                part.get(
                    "text",
                    "",
                )
                for part in parts
            )

        except (
            KeyError,
            IndexError,
            TypeError,
        ) as exc:

            raise LLMProviderResponseError(
                "Google AI returned an invalid response."
            ) from exc

        usage_metadata = (
            data.get(
                "usageMetadata"
            )
            or {}
        )

        input_tokens = int(
            usage_metadata.get(
                "promptTokenCount",
                0,
            )
        )

        output_tokens = int(
            usage_metadata.get(
                "candidatesTokenCount",
                0,
            )
        )

        total_tokens = int(
            usage_metadata.get(
                "totalTokenCount",
                input_tokens
                + output_tokens,
            )
        )

        return LLMResponse(
            content=content,
            usage=LLMUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
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
            json_mode=True,
        )

        try:

            response.parsed_json = json.loads(
                response.content
            )

        except json.JSONDecodeError as exc:

            raise LLMProviderResponseError(
                "Google AI returned invalid JSON."
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