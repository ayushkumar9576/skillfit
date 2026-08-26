"""
app/services/llm/config.py
--------------------------
Configuration for the SkillFit LLM Integration Layer (Phase 3.6).

Mirrors the project's existing configuration style (``os.getenv`` after
``load_dotenv`` — see ``app/db/database.py``) but packages the LLM-specific
settings into a small, testable dataclass.

Design:
    - **Provider-independent naming.** Generic runtime settings use the
      ``LLM_*`` prefix (``LLM_PROVIDER``, ``LLM_MODEL``, ``LLM_TIMEOUT``,
      ``LLM_MAX_RETRIES``). Swapping providers later does not require analyzer
      or service changes.
    - **Credentials are NOT stored here.** Provider-specific secrets such as
      ``OPENAI_API_KEY`` are read by the concrete provider itself
      (``openai_provider.py``), keeping this object free of secrets.
    - **Lazy validation.** ``validate()`` is invoked when the LLM service /
      provider is first constructed — never at import or app startup — so the
      app boots and existing tests run without any LLM configuration present.
"""

import os
from dataclasses import dataclass

from app.services.llm.exceptions import LLMConfigurationError

# Providers currently understood by the layer. Extend as new providers land
# (azure, anthropic, gemini, ...). Kept as a set for O(1) membership checks.
KNOWN_PROVIDERS: frozenset[str] = frozenset({"openai", "gemini"})

# Defaults (used when the corresponding env var is unset).
DEFAULT_PROVIDER: str = "openai"
DEFAULT_MODEL: str = "gpt-4o-mini"
DEFAULT_TIMEOUT: float = 30.0
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_RETRY_BASE_DELAY: float = 0.5
DEFAULT_RETRY_MAX_DELAY: float = 8.0


def _getenv_float(key: str, default: float) -> float:
    """Read a float env var, raising LLMConfigurationError on a non-numeric value."""
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise LLMConfigurationError(
            f"Environment variable {key} must be a number (got {raw!r})."
        ) from exc


def _getenv_int(key: str, default: int) -> int:
    """Read an int env var, raising LLMConfigurationError on a non-integer value."""
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise LLMConfigurationError(
            f"Environment variable {key} must be an integer (got {raw!r})."
        ) from exc


@dataclass
class LLMSettings:
    """
    Runtime settings for the LLM layer.

    Contains no secrets — the API key lives with the provider. Safe to log.
    """

    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL
    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_base_delay: float = DEFAULT_RETRY_BASE_DELAY
    retry_max_delay: float = DEFAULT_RETRY_MAX_DELAY

    @classmethod
    def from_env(cls) -> "LLMSettings":
        """
        Build settings from environment variables, applying defaults where unset.

        Raises:
            LLMConfigurationError: if a numeric variable holds a non-numeric value.
        """
        return cls(
            provider=(os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER) or DEFAULT_PROVIDER).strip().lower(),
            model=(os.getenv("LLM_MODEL", DEFAULT_MODEL) or DEFAULT_MODEL).strip(),
            timeout=_getenv_float("LLM_TIMEOUT", DEFAULT_TIMEOUT),
            max_retries=_getenv_int("LLM_MAX_RETRIES", DEFAULT_MAX_RETRIES),
            retry_base_delay=_getenv_float("LLM_RETRY_BASE_DELAY", DEFAULT_RETRY_BASE_DELAY),
            retry_max_delay=_getenv_float("LLM_RETRY_MAX_DELAY", DEFAULT_RETRY_MAX_DELAY),
        )

    def validate(self) -> None:
        """
        Fail-fast validation of the settings.

        Raises:
            LLMConfigurationError: on an unknown provider, empty model, or
                out-of-range numeric values.
        """
        if self.provider not in KNOWN_PROVIDERS:
            raise LLMConfigurationError(
                f"Unsupported LLM provider {self.provider!r}. "
                f"Known providers: {sorted(KNOWN_PROVIDERS)}."
            )
        if not self.model:
            raise LLMConfigurationError("LLM_MODEL must not be empty.")
        if self.timeout <= 0:
            raise LLMConfigurationError(
                f"LLM_TIMEOUT must be positive (got {self.timeout})."
            )
        if self.max_retries < 0:
            raise LLMConfigurationError(
                f"LLM_MAX_RETRIES must be >= 0 (got {self.max_retries})."
            )
        if self.retry_base_delay < 0 or self.retry_max_delay < 0:
            raise LLMConfigurationError("Retry delays must be non-negative.")
        if self.retry_max_delay < self.retry_base_delay:
            raise LLMConfigurationError(
                "LLM_RETRY_MAX_DELAY must be >= LLM_RETRY_BASE_DELAY."
            )


def validate_llm_config() -> LLMSettings:
    """
    Optional explicit startup check: build settings from the environment and
    validate them. Not called at import time; a deployment may call this during
    a health check or startup event to fail fast on misconfiguration.

    Returns:
        The validated LLMSettings instance.

    Raises:
        LLMConfigurationError: if the environment is misconfigured.
    """
    settings = LLMSettings.from_env()
    settings.validate()
    return settings
