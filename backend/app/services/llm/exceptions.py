"""
app/services/llm/exceptions.py
------------------------------
Custom exception hierarchy for the SkillFit LLM Integration Layer (Phase 3.6).

The LLM layer is *internal infrastructure* — it runs inside background pipeline
stages and analyzer engines, never directly inside a FastAPI request handler.
Following the convention established by
``extraction_service.extract_resume_internal`` (which raises ``ValueError`` /
``RuntimeError`` rather than ``HTTPException``), this layer raises plain Python
exceptions from a dedicated hierarchy. Request-scoped callers are responsible
for translating these into ``HTTPException`` if/when needed.

Hierarchy:
    LLMError                        (base — catch-all for the whole layer)
    ├── LLMConfigurationError       misconfiguration (bad/missing settings, no API key)
    ├── PromptNotFoundError         a requested prompt template file does not exist
    ├── PromptRenderError           a prompt template is missing a required placeholder
    ├── LLMResponseError            model returned invalid/unparseable/malformed output
    │                               (NON-retryable — retrying won't fix bad JSON)
    └── LLMProviderError            provider/transport failure; carries `.transient`
        ├── LLMTimeoutError         request exceeded the configured timeout (transient)
        └── LLMRateLimitError       provider rate limit hit (transient)

Security:
    Exception messages are sanitized — they NEVER embed the API key, prompt
    content, or raw model output. Callers log ``type(exc).__name__`` and the
    (safe) message, not provider internals.
"""


class LLMError(Exception):
    """Base class for every error raised by the LLM integration layer."""


class LLMConfigurationError(LLMError):
    """
    Raised when the LLM layer is misconfigured — e.g. an unknown provider,
    invalid numeric settings, or a missing ``OPENAI_API_KEY``.

    Raised lazily (at service/provider construction), never at import time,
    so the application can boot and existing tests can run without a key.
    """


class PromptNotFoundError(LLMError):
    """Raised when a requested prompt template file cannot be located on disk."""


class PromptRenderError(LLMError):
    """
    Raised when rendering a prompt template fails because a required
    placeholder was not supplied (or an invalid format field was referenced).
    """


class LLMResponseError(LLMError):
    """
    Raised when the model's response cannot be parsed as JSON or fails
    validation against the caller's Pydantic response schema.

    This is deliberately NOT a subclass of ``LLMProviderError`` and is
    therefore treated as **non-retryable** by the retry layer — re-issuing an
    identical request is unlikely to change malformed output.
    """


class LLMProviderError(LLMError):
    """
    Raised for provider-side / transport failures (connection errors, HTTP
    status errors, unexpected SDK errors).

    Attributes:
        transient: When ``True`` the failure is considered temporary and the
            retry layer may re-attempt the call (e.g. 5xx, connection drops).
            When ``False`` the failure is permanent for this request (e.g. 4xx,
            authentication) and must not be retried.
    """

    def __init__(self, message: str, *, transient: bool = False) -> None:
        super().__init__(message)
        self.transient: bool = transient


class LLMTimeoutError(LLMProviderError):
    """Raised when a provider request exceeds the configured timeout (transient)."""

    def __init__(self, message: str = "LLM request timed out.") -> None:
        super().__init__(message, transient=True)


class LLMRateLimitError(LLMProviderError):
    """Raised when the provider reports a rate-limit condition (transient)."""

    def __init__(self, message: str = "LLM provider rate limit exceeded.") -> None:
        super().__init__(message, transient=True)
