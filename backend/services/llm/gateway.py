import logging
from typing import Any, Dict, List, Optional

from backend.services.llm.base import (
    BaseLLMProvider,
)
from backend.services.llm.factory import (
    create_llm_provider,
)


logger = logging.getLogger("smarthire.llm.gateway")


class LLMGateway:
    """
    Central gateway for all SmartHire LLM operations.

    Interview services should use this class rather than
    talking directly to a provider.
    """

    def __init__(
        self,
        provider: str = "groq",
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.provider: BaseLLMProvider = (
            create_llm_provider(
                provider,
                api_key=api_key,
                model=model,
            )
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:

        return await self.provider.generate(
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
    ) -> Dict[str, Any]:

        return await self.provider.generate_json(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def is_configured(self) -> bool:
        return self.provider.is_configured()

    def get_provider_info(self) -> Dict[str, Any]:
        return self.provider.get_provider_info()