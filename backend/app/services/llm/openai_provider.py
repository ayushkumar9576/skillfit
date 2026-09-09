"""
app/services/llm/openai_provider.py
-----------------------------------
Concrete OpenAI provider for the SkillFit LLM Integration Layer (Phase 3.6).

Uses the official OpenAI Python SDK's async client (``AsyncOpenAI``) and
requests structured JSON output via ``response_format={"type": "json_object"}``,
then validates that JSON against the caller's Pydantic schema.

This is the ONLY module that imports the ``openai`` SDK. It is imported lazily
by ``base.get_llm_provider`` so the rest of the package (and app boot) never
depends on the SDK being installed or configured.

OpenAI-compatible gateways:
    Because the request/response shape is the OpenAI Chat Completions contract,
    the same provider can talk to ANY OpenAI-compatible endpoint — AgentRouter,
    OpenRouter-style services, AI-Studio gateways, Azure-OpenAI-compatible
    proxies, or a local proxy — by pointing it at a different base URL. Set
    ``OPENAI_BASE_URL`` (or pass ``base_url=``) and keep ``LLM_PROVIDER=openai``;
    choose the gateway's model via ``LLM_MODEL`` and its key via
    ``OPENAI_API_KEY``. No new provider class is required.

Security:
    - The API key is read from ``OPENAI_API_KEY`` and never logged or embedded
      in an exception message.
    - The base URL is logged as its *host only* (never the full URL), so any
      credential accidentally embedded in a gateway URL's path/query is not
      leaked to logs.
    - Error mapping logs only the exception *type* and transient flag, never
      raw SDK error text (which may include request metadata).

Retries/timeout:
    - The SDK client is created with ``max_retries=0`` — this layer owns retry
      policy (see ``retry.py``). ``timeout`` comes from ``LLMSettings`` and may
      be overridden per call.
"""

import logging
import os
from typing import Optional, Type
from urllib.parse import urlparse

from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)
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

# Canonical public OpenAI endpoint. Passed explicitly as the default so the SDK
# never independently re-reads OPENAI_BASE_URL from the environment — which would
# bypass this provider's own resolution (e.g. a stray "OPENAI_BASE_URL=   " would
# otherwise reach the SDK as a broken whitespace URL).
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


def _map_openai_exception(exc: Exception) -> LLMProviderError:
    """
    Translate an OpenAI SDK exception into this layer's provider-error hierarchy.

    Order matters: ``APITimeoutError`` is a subclass of ``APIConnectionError``
    and ``RateLimitError`` is a subclass of ``APIStatusError``, so the more
    specific types are checked first.
    """
    if isinstance(exc, APITimeoutError):
        return LLMTimeoutError()
    if isinstance(exc, RateLimitError):
        return LLMRateLimitError()
    if isinstance(exc, APIConnectionError):
        # Network/connection failure — worth retrying.
        return LLMProviderError("LLM provider connection error.", transient=True)
    if isinstance(exc, APIStatusError):
        status_code = getattr(exc, "status_code", None)
        # 5xx are transient; 4xx (auth, bad request, ...) are permanent.
        transient = status_code is not None and status_code >= 500
        return LLMProviderError(
            f"LLM provider returned HTTP status {status_code}.", transient=transient
        )
    if isinstance(exc, APIError):
        return LLMProviderError("LLM provider error.", transient=False)
    return LLMProviderError("Unexpected LLM provider error.", transient=False)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI-backed implementation of :class:`BaseLLMProvider`."""

    PROVIDER_NAME = "openai"

    def __init__(
        self,
        settings: Optional[LLMSettings] = None,
        client: Optional[AsyncOpenAI] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        """
        Args:
            settings: LLM runtime settings (built from env if omitted).
            client:   Pre-constructed ``AsyncOpenAI`` (or compatible) client.
                      When provided, the API-key / base-URL resolution is
                      bypassed entirely — this is the injection point used by
                      tests (no real key needed) and by callers that want full
                      control of the client (e.g. a pre-configured gateway).
            api_key:  Explicit API key; falls back to ``OPENAI_API_KEY`` env.
            base_url: Explicit OpenAI-compatible base URL; falls back to the
                      ``OPENAI_BASE_URL`` env var, else ``None`` (the SDK
                      default, ``https://api.openai.com/v1``). Setting this
                      routes every call through an OpenAI-compatible gateway
                      (AgentRouter, OpenRouter-style services, AI-Studio
                      gateways, a local proxy, …) WITHOUT a new provider class,
                      since the request/response contract is unchanged. Leave it
                      unset for the official OpenAI API (fully backward
                      compatible).

        Raises:
            LLMConfigurationError: if no client is injected and no API key is
                available.
        """
        self._settings = settings or LLMSettings.from_env()

        if client is not None:
            self._client = client
            return

        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise LLMConfigurationError(
                "OPENAI_API_KEY is not set. Add it to backend/.env "
                "(see backend/.env.example)."
            )

        # OpenAI-compatible gateway support. An explicit arg wins, then the
        # OPENAI_BASE_URL env var, else the canonical OpenAI endpoint.
        # Blank/whitespace is treated as unset. We ALWAYS pass base_url
        # explicitly: leaving it None makes the SDK re-read OPENAI_BASE_URL from
        # the environment itself, bypassing this resolution (and turning a stray
        # whitespace value into a broken URL).
        resolved_base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "").strip()
        print("OPENAI_BASE_URL =", resolved_base_url)
        # max_retries=0: retry policy is owned by this layer, not the SDK.
        self._client = AsyncOpenAI(
            api_key=key,
            base_url=resolved_base_url or DEFAULT_OPENAI_BASE_URL,
            timeout=self._settings.timeout,
            max_retries=0,
        )

        if resolved_base_url:
            # Log only the host — never the full URL — so a credential
            # accidentally embedded in the path/query is not leaked to logs.
            logger.info(
                "OpenAIProvider using custom OpenAI-compatible endpoint (host=%s).",
                urlparse(resolved_base_url).netloc or "unknown",
            )

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

        import json
        schema_json = response_schema.model_json_schema()
        enriched_system_prompt = (
            f"{system_prompt}\n\n"
            f"IMPORTANT: You MUST return a JSON object that strictly conforms to the following JSON Schema:\n"
            f"{json.dumps(schema_json, indent=2)}"
        )

        request_kwargs = {
            "model": use_model,
            "messages": [
                {"role": "system", "content": enriched_system_prompt},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": temperature,
        }
        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens
        if timeout is not None:
            request_kwargs["timeout"] = timeout

        try:
            print("\n===== LLM REQUEST DEBUG =====")
            print("MODEL:", use_model)
            print("SYSTEM PROMPT LENGTH:", len(system_prompt))
            print("USER CONTENT LENGTH:", len(user_content))
            print("MAX TOKENS:", max_tokens)
            print("TIMEOUT:", timeout or self._settings.timeout)
            print("=============================\n")
            print("1 - BEFORE OPENROUTER")
            response = await self._client.chat.completions.create(**request_kwargs)
            print("OPENROUTER RESPONSE RECEIVED")
        except (
            APITimeoutError,
            RateLimitError,
            APIConnectionError,
            APIStatusError,
            APIError,
        ) as exc:
            logger.exception("RAW OPENAI ERROR")
            raise _map_openai_exception(exc) from exc

        choice = response.choices[0] if getattr(response, "choices", None) else None
        content = choice.message.content if choice is not None else None

        usage_obj = getattr(response, "usage", None)
        prompt_tokens = int(getattr(usage_obj, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage_obj, "completion_tokens", 0) or 0)
        total_tokens = int(
            getattr(usage_obj, "total_tokens", 0) or (prompt_tokens + completion_tokens)
        )
        model_used = getattr(response, "model", None) or use_model

        # A response cut off at the output cap is valid JSON only up to the cut.
        # It is NOT retried: this layer requests temperature=0, so a second call
        # would deterministically truncate at the same point — paying for another
        # call to fail identically. Instead warn loudly (the budget is genuinely
        # too small) and let validate_response salvage the complete prefix, which
        # every analyzer schema tolerates.
        if choice is not None and getattr(choice, "finish_reason", None) == "length":
            logger.warning(
                "OpenAI response hit the output-token cap (max_tokens=%s, "
                "completion_tokens=%d) and was truncated. Salvaging a partial %s; "
                "raise LLM_MAX_TOKENS to avoid this.",
                max_tokens, completion_tokens, response_schema.__name__,
            )

        logger.debug(
            "OpenAI raw response (%d chars): %.2000s",
            len(content or ""), content or "",
        )
        # Enforce the JSON/schema contract (raises LLMResponseError on failure).
        print("STARTING STRUCTURED PARSE")
        parsed = validate_response(content, response_schema)
        print("STRUCTURED PARSE COMPLETE")
        usage = LLMUsage(
            provider=self.PROVIDER_NAME,
            model=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        print("RETURNING RESULT")
        return LLMCompletion(
            parsed=parsed,
            raw_text=content or "",
            usage=usage,
            provider=self.PROVIDER_NAME,
            model=model_used,
        )
