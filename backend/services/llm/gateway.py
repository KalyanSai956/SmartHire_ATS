import logging
from typing import Any, Dict, List, Optional

from backend.services.llm.base import (
    BaseLLMProvider,
    LLMResponse,
)

from backend.services.llm.factory import (
    create_llm_provider,
)

from backend.services.llm.usage import (
    record_llm_usage,
)


logger = logging.getLogger(
    "smarthire.llm.gateway"
)


class LLMGateway:

    def __init__(
        self,
        provider: str = "groq",
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        user_id: Optional[str] = None,
        feature: str = "general",
        usage_source: str = "platform",
    ):

        self.provider: BaseLLMProvider = (
            create_llm_provider(
                provider,
                api_key=api_key,
                model=model,
            )
        )

        self.user_id = user_id

        self.feature = (
            feature
            or "general"
        )

        self.usage_source = (
            usage_source
            or "platform"
        )

    # ========================================================
    # INTERNAL USAGE RECORDING
    # ========================================================

    async def _record_usage(
    self,
    response: LLMResponse,
) -> None:

        await record_llm_usage(
        user_id=self.user_id,
        usage=response.usage,
        provider=response.provider,
        model=response.model,
        feature=self.feature,
        usage_source=self.usage_source,
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

        response = await self.provider.generate(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        await self._record_usage(
            response
        )

        return response

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

        response = await self.provider.generate_json(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        await self._record_usage(
            response
        )

        return response

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def is_configured(
        self,
    ) -> bool:

        return self.provider.is_configured()

    # ========================================================
    # PROVIDER INFO
    # ========================================================

    def get_provider_info(
        self,
    ) -> Dict[str, Any]:

        return self.provider.get_provider_info()