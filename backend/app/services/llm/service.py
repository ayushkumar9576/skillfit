"""
app/services/llm/service.py
---------------------------
Central LLM service for the SkillFit LLM Integration Layer (Phase 3.6).

This is the single entry point every future analyzer (Projects 3.7,
Internships 3.8, Certifications 3.9, Achievements, Skills 3.10) calls. Analyzers
never touch a provider SDK directly — they call ``analyze(...)`` and receive a
validated Pydantic object back.

Responsibilities:
    - Resolve and render the analyzer's prompt (via :class:`PromptManager`).
    - JSON-encode the input evidence as the user message.
    - Delegate the actual completion to the configured provider, wrapped in the
      transient-only retry policy.
    - Record usage (analyzer + response-schema name + provider/model).
    - Return the validated ``response_schema`` instance.

Async boundary:
    ``analyze`` is ``async`` and awaits throughout. There is NO ``asyncio.run``
    here — the async→sync bridge belongs to the outer orchestrator (the pipeline
    stage in Phase 3.7+, or the test harness today).

Dependency injection:
    Every collaborator (provider, prompt manager, usage tracker, settings) can
    be injected, which is what makes the layer unit-testable without any network
    access or real API key.
"""

import json
import logging
from typing import Any, Optional, Type

from pydantic import BaseModel

from app.services.llm.base import BaseLLMProvider, get_llm_provider
from app.services.llm.config import LLMSettings
from app.services.llm.prompt_manager import PromptManager, default_prompt_manager
from app.services.llm.retry import with_retry
from app.services.llm.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


class LLMService:
    """Provider-agnostic orchestrator for structured LLM analysis."""

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        prompt_manager: Optional[PromptManager] = None,
        usage_tracker: Optional[UsageTracker] = None,
        settings: Optional[LLMSettings] = None,
    ) -> None:
        """
        Construct the service, validating configuration lazily (fail-fast here,
        never at import/app-boot).

        When ``provider`` is injected, no provider is constructed from config,
        so a real ``OPENAI_API_KEY`` is not required (used by tests).

        Raises:
            LLMConfigurationError: if settings are invalid, or if a provider must
                be constructed from config but is misconfigured.
        """
        self._settings = settings or LLMSettings.from_env()
        self._settings.validate()

        self._provider = provider or get_llm_provider(
            self._settings.provider, self._settings
        )
        self._prompts = prompt_manager or default_prompt_manager
        self._usage = usage_tracker or UsageTracker()

    @property
    def usage_tracker(self) -> UsageTracker:
        """Expose the usage tracker (useful for inspection and tests)."""
        return self._usage

    async def analyze(
        self,
        *,
        analyzer: str,
        data: Any,
        response_schema: Type[BaseModel],
        prompt_name: Optional[str] = None,
        prompt_vars: Optional[dict] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> BaseModel:
        """
        Run one structured analysis.

        Args:
            analyzer:        Logical analyzer name (e.g. ``"project"``). Selects
                             the default prompt ``"{analyzer}_analysis"`` and
                             labels the usage record.
            data:            JSON-serializable evidence sent as the user message.
            response_schema: Pydantic model the response is validated against.
            prompt_name:     Override the prompt template name.
            prompt_vars:     Extra values for prompt placeholders. ``schema_name``
                             is always supplied automatically.
            model / temperature / max_tokens / timeout: per-call provider overrides.

        Returns:
            A validated instance of ``response_schema``.

        Raises:
            PromptNotFoundError / PromptRenderError: prompt issues.
            LLMResponseError: invalid/malformed model output.
            LLMProviderError (and subclasses): provider failures after retries.
        """
        schema_name = getattr(response_schema, "__name__", str(response_schema))
        template_name = prompt_name or f"{analyzer}_analysis"

        render_vars = {"schema_name": schema_name}
        if prompt_vars:
            render_vars.update(prompt_vars)
        system_prompt = self._prompts.render(template_name, **render_vars)

        user_content = json.dumps(data, ensure_ascii=False, default=str)

        completion = await with_retry(
            lambda: self._provider.complete_structured(
                system_prompt=system_prompt,
                user_content=user_content,
                response_schema=response_schema,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            ),
            max_retries=self._settings.max_retries,
            base_delay=self._settings.retry_base_delay,
            max_delay=self._settings.retry_max_delay,
        )

        # Record usage with full traceability: which analyzer, which schema,
        # and the exact provider/model that produced the result.
        self._usage.record(
            analyzer=analyzer,
            schema_name=schema_name,
            provider=completion.provider,
            model=completion.model,
            prompt_tokens=completion.usage.prompt_tokens,
            completion_tokens=completion.usage.completion_tokens,
            total_tokens=completion.usage.total_tokens,
        )

        return completion.parsed


# ---------------------------------------------------------------------------
# Lazy singleton accessor
# ---------------------------------------------------------------------------
#
# The service is NOT constructed at import time (that would validate config and
# require a key, breaking app boot / existing tests). It is built on first use.

_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """
    Return the process-wide :class:`LLMService`, constructing it on first call.

    Raises:
        LLMConfigurationError: if the environment is misconfigured (e.g. no
            ``OPENAI_API_KEY``) when the service is first built.
    """
    global _llm_service
    _llm_service = LLMService()
    return _llm_service
