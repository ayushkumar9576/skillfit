"""
app/services/llm/__init__.py
----------------------------
Public surface of the SkillFit LLM Integration Layer (Phase 3.6).

Analyzers (Phase 3.7+) interact with this package ONLY — never with a provider
SDK directly. The typical call site is::

    from app.services.llm import get_llm_service, StructuredAnalysis

    service = get_llm_service()
    result = await service.analyze(
        analyzer="project",
        data=project_evidence,
        response_schema=StructuredAnalysis,   # or an analyzer-specific schema
    )

Importing this package is side-effect free: it does NOT construct the service,
build a provider, import the ``openai`` SDK, or require an API key. The service
is created lazily on the first ``get_llm_service()`` / ``llm_service`` access.
"""

from app.services.llm.base import BaseLLMProvider, LLMCompletion, get_llm_provider
from app.services.llm.config import LLMSettings, validate_llm_config
from app.services.llm.exceptions import (
    LLMConfigurationError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
    PromptNotFoundError,
    PromptRenderError,
)
from app.services.llm.prompt_manager import PromptManager, default_prompt_manager
from app.services.llm.retry import with_retry
from app.services.llm.schemas import (
    Evidence,
    Finding,
    LLMUsage,
    StructuredAnalysis,
    validate_response,
)
from app.services.llm.service import LLMService, get_llm_service
from app.services.llm.usage_tracker import LLMUsageRecord, UsageTracker, estimate_cost

__all__ = [
    # service
    "LLMService",
    "get_llm_service",
    "llm_service",
    # provider abstraction
    "BaseLLMProvider",
    "LLMCompletion",
    "get_llm_provider",
    # config
    "LLMSettings",
    "validate_llm_config",
    # prompts
    "PromptManager",
    "default_prompt_manager",
    # schemas
    "Evidence",
    "Finding",
    "StructuredAnalysis",
    "LLMUsage",
    "validate_response",
    # usage
    "UsageTracker",
    "LLMUsageRecord",
    "estimate_cost",
    # retry
    "with_retry",
    # exceptions
    "LLMError",
    "LLMConfigurationError",
    "PromptNotFoundError",
    "PromptRenderError",
    "LLMResponseError",
    "LLMProviderError",
    "LLMTimeoutError",
    "LLMRateLimitError",
]


def __getattr__(name: str):
    """
    Lazily expose ``llm_service`` as a module attribute (PEP 562) without
    constructing it at import time. ``from app.services.llm import llm_service``
    builds the singleton on demand via :func:`get_llm_service`.
    """
    if name == "llm_service":
        return get_llm_service()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
