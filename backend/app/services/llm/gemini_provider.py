"""
app/services/llm/gemini_provider.py
-----------------------------------
Concrete Gemini provider for the SkillFit LLM Integration Layer (Phase 3.6.1).
"""

import logging
import os
from typing import Optional, Type

from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel

from app.services.llm.base import BaseLLMProvider, LLMCompletion
from app.services.llm.config import LLMSettings
from app.services.llm.exceptions import (
    LLMConfigurationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.services.llm.schemas import LLMUsage, validate_response

logger = logging.getLogger(__name__)


def _hit_token_cap(response) -> bool:
    """
    Return ``True`` when Gemini stopped because it ran out of output tokens.

    ``finish_reason`` is an SDK enum (``types.FinishReason.MAX_TOKENS``), so the
    check goes through its string name rather than an identity comparison — that
    keeps working across SDK versions and if the field arrives as a plain string.
    Never raises: a missing/odd candidate simply reads as "not truncated".
    """
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        reason = getattr(candidate, "finish_reason", None)
        if reason is None:
            continue
        name = getattr(reason, "name", None) or str(reason)
        if "MAX_TOKENS" in name.upper():
            return True
    return False


def _map_gemini_exception(exc: Exception) -> LLMProviderError:
    """Translate a Gemini SDK exception into this layer's provider-error hierarchy."""
    import httpx
    import asyncio
    
    if isinstance(exc, (httpx.TimeoutException, asyncio.TimeoutError)):
        return LLMTimeoutError()
        
    if isinstance(exc, APIError):
        code = getattr(exc, "code", None)
        message = str(getattr(exc, "message", "") or str(exc)).lower()
        status = getattr(exc, "status", None)
        
        if code == 429 or status == 429 or "rate limit" in message or "429" in message:
            return LLMRateLimitError()
            
        if code == 401 or code == 403 or "auth" in message or "api key" in message:
            return LLMProviderError("LLM provider authentication error.", transient=False)
            
        # 5xx are transient; 4xx are permanent.
        if code is not None and isinstance(code, int):
            transient = code >= 500
            return LLMProviderError(f"Gemini API returned status {code}.", transient=transient)
            
        if status is not None and isinstance(status, int):
            transient = status >= 500
            return LLMProviderError(f"Gemini API returned status {status}.", transient=transient)
            
        # Assume other API errors are not transient unless specified
        return LLMProviderError("Gemini provider error.", transient=False)
        
    if isinstance(exc, httpx.RequestError):
        return LLMProviderError("Gemini provider connection error.", transient=True)
        
    return LLMProviderError("Unexpected Gemini provider error.", transient=False)


class GeminiProvider(BaseLLMProvider):
    """Gemini-backed implementation of :class:`BaseLLMProvider`."""

    PROVIDER_NAME = "gemini"

    def __init__(
        self,
        settings: Optional[LLMSettings] = None,
        client: Optional[genai.Client] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self._settings = settings or LLMSettings.from_env()

        if client is not None:
            self._client = client
            return

        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise LLMConfigurationError(
                "GEMINI_API_KEY is not set. Add it to backend/.env "
                "(see backend/.env.example)."
            )

        self._client = genai.Client(api_key=key, http_options={"timeout": self._settings.timeout * 1000})

    async def complete_structured(
        self,
        *,
        system_prompt: str,
        user_content: str,
        response_schema: Type[BaseModel],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> LLMCompletion:
        use_model = model or self._settings.model

        config_kwargs = {
            "response_mime_type": "application/json",
            "temperature": temperature,
            "system_instruction": system_prompt,
        }
        # Only set a cap when the caller gave one, mirroring the OpenAI provider.
        # (Previously a hardcoded 16384 default silently overrode the budget the
        # analysis engine had resolved.)
        if max_tokens is not None:
            config_kwargs["max_output_tokens"] = max_tokens

        contents = [
            user_content
        ]

        try:
            response = await self._client.aio.models.generate_content(
                model=use_model,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            print("\n=== RAW GEMINI RESPONSE ===")
            print(response.text)
            print("==========================\n")
        except Exception as exc:
            mapped = _map_gemini_exception(exc)
            logger.warning(
                "Gemini request failed: %s (transient=%s).",
                type(exc).__name__,
                mapped.transient,
            )
            raise mapped from exc

        content = response.text if response else None

        usage_obj = getattr(response, "usage_metadata", None)
        prompt_tokens = int(getattr(usage_obj, "prompt_token_count", 0) or 0)
        completion_tokens = int(getattr(usage_obj, "candidates_token_count", 0) or 0)
        total_tokens = int(getattr(usage_obj, "total_token_count", 0) or (prompt_tokens + completion_tokens))

        # See the OpenAI provider for why truncation is salvaged rather than
        # retried: temperature is 0, so a second call truncates identically.
        if _hit_token_cap(response):
            logger.warning(
                "Gemini response hit the output-token cap (max_output_tokens=%s, "
                "candidates_token_count=%d) and was truncated. Salvaging a partial "
                "%s; raise LLM_MAX_TOKENS to avoid this.",
                max_tokens, completion_tokens, response_schema.__name__,
            )

        logger.debug(
            "Gemini raw response (%d chars): %.2000s",
            len(content or ""), content or "",
        )
        parsed = validate_response(content, response_schema)

        usage = LLMUsage(
            provider=self.PROVIDER_NAME,
            model=use_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        return LLMCompletion(
            parsed=parsed,
            raw_text=content or "",
            usage=usage,
            provider=self.PROVIDER_NAME,
            model=use_model,
        )
