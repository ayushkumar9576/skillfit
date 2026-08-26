"""
scripts/test_gemini_provider.py
-------------------------------
Verification suite for Phase 3.6.1 - Gemini Provider Integration.

Mock-only: NO network calls and NO real Gemini API key are required. Every
provider interaction is exercised through an injected fake client, and every
Gemini error path is exercised by constructing the SDK's own exception types locally.
"""

import asyncio
import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, ".")

from pydantic import BaseModel, ConfigDict
import httpx

from google.genai.errors import APIError

from app.services.llm.base import LLMCompletion, get_llm_provider
from app.services.llm.config import LLMSettings
from app.services.llm.exceptions import (
    LLMConfigurationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)
from app.services.llm.gemini_provider import GeminiProvider, _map_gemini_exception

errors = []

def check(label, cond, detail=""):
    ok = bool(cond)
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        errors.append(f"{label}: {detail}" if detail else label)


def expect_raises(label, exc_type, thunk):
    """Assert that calling ``thunk()`` raises ``exc_type`` (or a subclass)."""
    try:
        thunk()
    except exc_type:
        print(f"PASS  {label}")
    except Exception as exc:  # wrong exception type
        print(f"FAIL  {label}")
        errors.append(
            f"{label}: expected {exc_type.__name__}, got {type(exc).__name__}: {exc}"
        )
    else:  # nothing raised
        print(f"FAIL  {label}")
        errors.append(f"{label}: expected {exc_type.__name__}, nothing raised")


def run(coro):
    """Drive a coroutine to completion."""
    return asyncio.run(coro)


class _Sample(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    score: float


# ---------------------------------------------------------------------------
print("\n--- 1. Exception mapping ---")

check(
    "_map_gemini_exception: TimeoutException -> LLMTimeoutError",
    isinstance(_map_gemini_exception(httpx.TimeoutException("timeout")), LLMTimeoutError),
)

err_429 = APIError("rate limit exceeded", 429, None)
err_429.code = 429

check(
    "_map_gemini_exception: APIError(429) -> LLMRateLimitError",
    isinstance(_map_gemini_exception(err_429), LLMRateLimitError),
)

err_401 = APIError("auth failed", 401, None)
err_401.code = 401

check(
    "_map_gemini_exception: APIError(401) -> non-transient LLMProviderError",
    _map_gemini_exception(err_401).transient is False,
)

err_503 = APIError("server overloaded", 503, None)
err_503.code = 503

check(
    "_map_gemini_exception: APIError(503) -> transient LLMProviderError",
    _map_gemini_exception(err_503).transient is True,
)

# ---------------------------------------------------------------------------
print("\n--- 2. Fake Client / Provider Tests ---")

def fake_response(content, prompt_tokens=11, completion_tokens=7, total_tokens=18):
    return SimpleNamespace(
        text=content,
        usage_metadata=SimpleNamespace(
            prompt_token_count=prompt_tokens,
            candidates_token_count=completion_tokens,
            total_token_count=total_tokens,
        )
    )

class FakeModels:
    def __init__(self, result=None, exc=None):
        self._result = result
        self._exc = exc
        self.last_kwargs = None
        
    async def generate_content(self, **kwargs):
        self.last_kwargs = kwargs
        if self._exc is not None:
            raise self._exc
        return self._result

class FakeAio:
    def __init__(self, result=None, exc=None):
        self.models = FakeModels(result=result, exc=exc)

class FakeGeminiClient:
    def __init__(self, result=None, exc=None):
        self.aio = FakeAio(result=result, exc=exc)


settings = LLMSettings()

# --- successful completion ---
prov = GeminiProvider(
    settings=settings,
    client=FakeGeminiClient(result=fake_response(json.dumps({"name": "proj", "score": 0.8}))),
)
comp = run(
    prov.complete_structured(
        system_prompt="system", user_content="user", response_schema=_Sample, model="gemini-2.5-flash"
    )
)
check(
    "provider: returns LLMCompletion with parsed schema",
    isinstance(comp, LLMCompletion)
    and isinstance(comp.parsed, _Sample)
    and comp.parsed.name == "proj"
    and comp.parsed.score == 0.8,
)
check(
    "provider: LLMCompletion carries provider + model",
    comp.provider == "gemini" and comp.model == "gemini-2.5-flash",
)
check(
    "provider: sent system instruction",
    prov._client.aio.models.last_kwargs["config"].system_instruction == "system",
)

# --- invalid response ---
prov_bad = GeminiProvider(
    settings=settings, client=FakeGeminiClient(result=fake_response("not-json"))
)
expect_raises(
    "provider: non-JSON content -> LLMResponseError",
    LLMResponseError,
    lambda: run(
        prov_bad.complete_structured(
            system_prompt="s", user_content="u", response_schema=_Sample
        )
    ),
)

# --- exceptions ---
def raising_provider(exc):
    return GeminiProvider(settings=settings, client=FakeGeminiClient(exc=exc))

expect_raises(
    "provider: Timeout -> LLMTimeoutError",
    LLMTimeoutError,
    lambda: run(
        raising_provider(httpx.TimeoutException("timeout")).complete_structured(
            system_prompt="s", user_content="u", response_schema=_Sample
        )
    ),
)

expect_raises(
    "provider: 429 -> LLMRateLimitError",
    LLMRateLimitError,
    lambda: run(
        raising_provider(err_429).complete_structured(
            system_prompt="s", user_content="u", response_schema=_Sample
        )
    ),
)

expect_raises(
    "provider: 401 -> LLMProviderError",
    LLMProviderError,
    lambda: run(
        raising_provider(err_401).complete_structured(
            system_prompt="s", user_content="u", response_schema=_Sample
        )
    ),
)

# --- API key missing ---
saved_key = os.environ.pop("GEMINI_API_KEY", None)
try:
    expect_raises(
        "provider: missing GEMINI_API_KEY -> LLMConfigurationError",
        LLMConfigurationError,
        lambda: GeminiProvider(settings=settings),
    )
finally:
    if saved_key is not None:
        os.environ["GEMINI_API_KEY"] = saved_key

# ---------------------------------------------------------------------------
print("\n--- 3. get_llm_provider factory ---")

saved_key = os.environ.pop("GEMINI_API_KEY", None)
try:
    expect_raises(
        "factory: gemini routes to GeminiProvider (no key -> LLMConfigurationError)",
        LLMConfigurationError,
        lambda: get_llm_provider("gemini"),
    )
finally:
    if saved_key is not None:
        os.environ["GEMINI_API_KEY"] = saved_key

if errors:
    print(f"\nFAILED: {len(errors)} errors:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\nALL PASSED.")
    sys.exit(0)
