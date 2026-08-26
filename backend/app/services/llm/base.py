"""
app/services/llm/base.py
------------------------
Provider abstraction for the SkillFit LLM Integration Layer (Phase 3.6).

Mirrors the Strategy + Factory pattern already used for section detection
(``app/services/resume/section_detector.py``: ``BaseSectionDetector`` (ABC) →
concrete impls → ``get_section_detector(type)``). Analyzers depend ONLY on this
abstraction, never on a concrete SDK, so migrating to Azure OpenAI / Anthropic
/ Gemini later requires no analyzer changes.

Contains no provider-specific code: the OpenAI implementation lives in
``openai_provider.py`` and is imported lazily by the factory so that importing
this module (and the wider ``app.services.llm`` package) never requires the
``openai`` SDK or an API key.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Type, TYPE_CHECKING

from pydantic import BaseModel

from app.services.llm.exceptions import LLMConfigurationError
from app.services.llm.schemas import LLMUsage

if TYPE_CHECKING:  # avoid a runtime import cycle / cost; only for type hints
    from app.services.llm.config import LLMSettings


@dataclass
class LLMCompletion:
    """
    Normalized result of a single structured completion, independent of provider.

    Attributes:
        parsed:    The validated Pydantic object (an instance of the caller's
                   ``response_schema``).
        raw_text:  The raw JSON string the provider returned (for auditing/debug).
        usage:     Token usage + provenance for this call.
        provider:  Provider that produced the completion (e.g. ``"openai"``).
        model:     Concrete model that produced the completion.

    ``provider`` and ``model`` are surfaced here (in addition to ``usage``) so
    every analysis result can be traced back to the exact provider/model.
    """

    parsed: BaseModel
    raw_text: str
    usage: LLMUsage
    provider: str
    model: str


class BaseLLMProvider(ABC):
    """
    Abstract interface every LLM provider must implement.

    A provider's sole responsibility is: given a system prompt, user content,
    and a target Pydantic schema, return a validated :class:`LLMCompletion`.
    It owns provider-specific request construction and error mapping (to the
    ``app.services.llm.exceptions`` hierarchy) — nothing else.
    """

    @abstractmethod
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
        """
        Perform a structured (JSON) completion and validate it against
        ``response_schema``.

        Args:
            system_prompt:   The system/instruction prompt.
            user_content:    The user message (typically JSON-encoded evidence).
            response_schema: Pydantic model the response must conform to.
            model:           Optional per-call model override.
            temperature:     Sampling temperature (default 0.0 for determinism).
            max_tokens:      Optional cap on generated tokens.
            timeout:         Optional per-call timeout override (seconds).

        Returns:
            A validated :class:`LLMCompletion`.

        Raises:
            LLMResponseError:  invalid JSON / schema mismatch (non-retryable).
            LLMTimeoutError / LLMRateLimitError / LLMProviderError: provider
                failures (``.transient`` indicates retryability).
        """
        raise NotImplementedError


def get_llm_provider(
    provider_type: str = "openai",
    settings: "Optional[LLMSettings]" = None,
) -> BaseLLMProvider:
    """
    Factory returning a concrete provider instance.

    Mirrors ``get_section_detector``; the concrete provider module is imported
    lazily so this package does not require the ``openai`` SDK unless a provider
    is actually requested.

    Args:
        provider_type: Provider identifier (currently only ``"openai"``).
        settings:      Optional :class:`LLMSettings`; the provider builds its
                       own from the environment if omitted.

    Returns:
        A :class:`BaseLLMProvider` implementation.

    Raises:
        LLMConfigurationError: if ``provider_type`` is unknown. (The LLM layer
            uses its own exception hierarchy rather than ``ValueError``.)
    """
    normalized = (provider_type or "openai").strip().lower()

    if normalized == "openai":
        from app.services.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(settings=settings)
    elif normalized == "gemini":
        from app.services.llm.gemini_provider import GeminiProvider

        return GeminiProvider(settings=settings)

    raise LLMConfigurationError(
        f"Unsupported LLM provider {provider_type!r}. Available providers: 'openai', 'gemini'."
    )
