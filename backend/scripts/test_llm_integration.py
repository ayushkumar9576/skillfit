"""
scripts/test_llm_integration.py
-------------------------------
Verification suite for Phase 3.6 - LLM Integration Layer.

Mock-only: NO network calls and NO real OpenAI API key are required. Every
provider interaction is exercised through an injected fake client / fake
provider, and every OpenAI error path is exercised by constructing the SDK's
own exception types locally. Async code is driven by ``asyncio.run`` ONLY here
in the test harness (the sanctioned outer boundary) - never inside the
``app/services/llm`` package.

Run from the ``backend`` directory:

    python scripts/test_llm_integration.py

Mirrors the existing standalone-script convention (errors[] / PASS-FAIL /
sys.exit(1)) used by scripts/test_extraction.py.
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, ".")

from pydantic import BaseModel, ConfigDict

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
from app.services.llm.openai_provider import OpenAIProvider, _map_openai_exception
from app.services.llm.prompt_manager import PromptManager, default_prompt_manager
from app.services.llm.retry import with_retry
from app.services.llm.schemas import (
    Evidence,
    Finding,
    LLMUsage,
    StructuredAnalysis,
    _repair_truncated_json,
    validate_response,
)
from app.services.llm.service import LLMService
from app.services.llm.usage_tracker import UsageTracker, estimate_cost

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
    """Drive a coroutine to completion. asyncio.run lives ONLY in the harness."""
    return asyncio.run(coro)


class _CaptureHandler(logging.Handler):
    """Collect emitted records so a log-only code path can be asserted on."""

    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def captured_warnings(logger_name, thunk):
    """Run ``thunk()`` and return the WARNING+ messages ``logger_name`` emitted."""
    target = logging.getLogger(logger_name)
    handler = _CaptureHandler()
    previous_level = target.level
    target.addHandler(handler)
    target.setLevel(logging.DEBUG)
    try:
        thunk()
    finally:
        target.removeHandler(handler)
        target.setLevel(previous_level)
    return [r.getMessage() for r in handler.records if r.levelno >= logging.WARNING]


class _Sample(BaseModel):
    """Minimal response schema used across provider/service tests."""

    model_config = ConfigDict(extra="ignore")

    name: str
    score: float


# ---------------------------------------------------------------------------
print("\n--- 1. Exception hierarchy & transient flags ---")

check("LLMTimeoutError is transient", LLMTimeoutError().transient is True)
check("LLMRateLimitError is transient", LLMRateLimitError().transient is True)
check(
    "LLMProviderError defaults to non-transient",
    LLMProviderError("boom").transient is False,
)
check(
    "LLMProviderError(transient=True) honored",
    LLMProviderError("boom", transient=True).transient is True,
)
check(
    "LLMResponseError is not a provider error (never retried)",
    not issubclass(LLMResponseError, LLMProviderError),
)
check(
    "all custom errors subclass LLMError",
    all(
        issubclass(c, LLMError)
        for c in (
            LLMConfigurationError,
            PromptNotFoundError,
            PromptRenderError,
            LLMResponseError,
            LLMProviderError,
            LLMTimeoutError,
            LLMRateLimitError,
        )
    ),
)


# ---------------------------------------------------------------------------
print("\n--- 2. LLMSettings / config ---")

defaults = LLMSettings()
check("default provider is openai", defaults.provider == "openai")
check("default model is gpt-4o-mini", defaults.model == "gpt-4o-mini")
defaults.validate()  # must not raise
check("default settings pass validate()", True)

expect_raises(
    "unknown provider rejected",
    LLMConfigurationError,
    lambda: LLMSettings(provider="acme").validate(),
)
expect_raises(
    "non-positive timeout rejected",
    LLMConfigurationError,
    lambda: LLMSettings(timeout=0).validate(),
)
expect_raises(
    "negative max_retries rejected",
    LLMConfigurationError,
    lambda: LLMSettings(max_retries=-1).validate(),
)
expect_raises(
    "retry_max_delay < retry_base_delay rejected",
    LLMConfigurationError,
    lambda: LLMSettings(retry_base_delay=5.0, retry_max_delay=1.0).validate(),
)

# from_env() reads the generic LLM_* namespace deterministically.
os.environ["LLM_PROVIDER"] = "openai"
os.environ["LLM_MODEL"] = "gpt-4o-mini"
os.environ["LLM_TIMEOUT"] = "30"
os.environ["LLM_MAX_RETRIES"] = "3"
from_env = LLMSettings.from_env()
from_env.validate()
check(
    "from_env() reads LLM_* vars",
    from_env.provider == "openai"
    and from_env.model == "gpt-4o-mini"
    and from_env.timeout == 30.0
    and from_env.max_retries == 3,
    detail=repr(from_env),
)

# Malformed numeric env var -> LLMConfigurationError (not a raw ValueError).
os.environ["LLM_TIMEOUT"] = "not-a-number"
expect_raises(
    "malformed LLM_TIMEOUT -> LLMConfigurationError",
    LLMConfigurationError,
    lambda: LLMSettings.from_env(),
)
os.environ["LLM_TIMEOUT"] = "30"  # restore

cfg = validate_llm_config()
check("validate_llm_config() returns validated settings", cfg.provider == "openai")

# Secrets must never appear in repr (defense-in-depth: settings hold no key).
check(
    "settings repr contains no api key material",
    "sk-" not in repr(defaults) and "key" not in repr(defaults).lower(),
    detail=repr(defaults),
)


# ---------------------------------------------------------------------------
print("\n--- 3. PromptManager (load / render / cache / exists) ---")

tmpdir = tempfile.mkdtemp()
with open(os.path.join(tmpdir, "sample_analysis.txt"), "w", encoding="utf-8") as fh:
    fh.write('Return JSON for {schema_name}. Shape: {{"k": "v"}}')
pm = PromptManager(prompts_dir=tmpdir)

loaded = pm.load("sample_analysis")
check("load() returns raw template text", "{schema_name}" in loaded)

rendered = pm.render("sample_analysis", schema_name="MySchema")
check(
    "render() substitutes placeholder and unescapes literal braces",
    rendered == 'Return JSON for MySchema. Shape: {"k": "v"}',
    detail=repr(rendered),
)

check("exists() True for present template", pm.exists("sample_analysis") is True)
check("has_prompt() alias True for present template", pm.has_prompt("sample_analysis") is True)
check("exists() False for missing template", pm.exists("does_not_exist") is False)

expect_raises(
    "load() missing -> PromptNotFoundError",
    PromptNotFoundError,
    lambda: pm.load("nope"),
)

with open(os.path.join(tmpdir, "needs_var.txt"), "w", encoding="utf-8") as fh:
    fh.write("Hello {name}, analyze for {schema_name}.")
expect_raises(
    "render() missing placeholder -> PromptRenderError",
    PromptRenderError,
    lambda: pm.render("needs_var", schema_name="X"),
)

# Cache: disk is read once; template survives file deletion.
cache_path = os.path.join(tmpdir, "cache_me.txt")
with open(cache_path, "w", encoding="utf-8") as fh:
    fh.write("cached {schema_name}")
first = pm.load("cache_me")
os.remove(cache_path)
second = pm.load("cache_me")
check(
    "template cached (served after underlying file deleted)",
    first == second == "cached {schema_name}",
)
check("exists() True from cache even after file deleted", pm.exists("cache_me") is True)


# ---------------------------------------------------------------------------
print("\n--- 4. Shipped prompt templates render cleanly ---")

for stem in ("project", "internship", "certification", "achievement", "skill"):
    tname = f"{stem}_analysis"
    check(f"shipped prompt exists: {tname}", default_prompt_manager.exists(tname))
    try:
        text = default_prompt_manager.render(tname, schema_name="StructuredAnalysis")
        check(
            f"shipped prompt renders with schema_name: {tname}",
            "StructuredAnalysis" in text,
        )
    except Exception as exc:  # a stray single brace would surface here
        check(f"shipped prompt renders with schema_name: {tname}", False, detail=str(exc))


# ---------------------------------------------------------------------------
print("\n--- 5. validate_response (structured-output enforcement) ---")

ok = validate_response(
    json.dumps({"name": "a", "score": 0.5, "extra": "ignored"}), _Sample
)
check(
    "validate_response returns typed model (extra ignored)",
    isinstance(ok, _Sample) and ok.name == "a" and ok.score == 0.5,
)
expect_raises(
    "invalid JSON -> LLMResponseError",
    LLMResponseError,
    lambda: validate_response("{not json", _Sample),
)
expect_raises(
    "schema mismatch -> LLMResponseError",
    LLMResponseError,
    lambda: validate_response(json.dumps({"name": "a"}), _Sample),
)
expect_raises(
    "empty response -> LLMResponseError",
    LLMResponseError,
    lambda: validate_response("", _Sample),
)

sa = validate_response(
    json.dumps(
        {
            "summary": "ok",
            "findings": [
                {
                    "statement": "s",
                    "confidence": 0.7,
                    "evidence": [
                        {"text": "t", "source_section": "projects", "confidence": 0.9}
                    ],
                }
            ],
        }
    ),
    StructuredAnalysis,
)
check(
    "StructuredAnalysis parses nested findings/evidence",
    len(sa.findings) == 1
    and isinstance(sa.findings[0], Finding)
    and isinstance(sa.findings[0].evidence[0], Evidence)
    and sa.findings[0].evidence[0].source_section == "projects",
)

# --- a response cut off at the output cap is salvaged, not lost ---
# Truncated text is valid JSON up to the cut, and analyzer schemas are
# optional-with-default throughout, so recovering the complete prefix beats
# discarding a whole analysis over the last few characters.
truncated = '{"name": "proj", "score": 0.8, "notes": "cut mid-sent'
salvaged = validate_response(truncated, _Sample)
check(
    "validate_response salvages a truncated response",
    isinstance(salvaged, _Sample) and salvaged.name == "proj" and salvaged.score == 0.8,
)
check(
    "_repair_truncated_json cuts before the incomplete element",
    json.loads(_repair_truncated_json(truncated)) == {"name": "proj", "score": 0.8},
    detail=repr(_repair_truncated_json(truncated)),
)
check(
    "_repair_truncated_json returns None for text that was never JSON",
    _repair_truncated_json("the model wrote an apology instead of an object") is None,
)

# Nested containers: the finished list element survives, the half-written one is
# dropped along with the key it had started.
nested_cut = (
    '{"summary": "ok", "findings": [{"statement": "first", "confidence": 0.7},'
    ' {"statement": "second half-writ'
)
nested = validate_response(nested_cut, StructuredAnalysis)
check(
    "validate_response salvage keeps complete nested items, drops the partial one",
    nested.summary == "ok"
    and len(nested.findings) == 1
    and nested.findings[0].statement == "first",
    detail=f"{len(nested.findings)} finding(s)",
)
check(
    "validate_response logs a WARNING when it has to salvage",
    any(
        "salvag" in m.lower()
        for m in captured_warnings(
            "app.services.llm.schemas",
            lambda: validate_response(truncated, _Sample),
        )
    ),
)


# ---------------------------------------------------------------------------
print("\n--- 6. with_retry (transient-only, injectable sleep) ---")


def make_sleep(sink):
    async def _sleep(delay):
        sink.append(delay)

    return _sleep


# Succeeds after one transient failure.
calls = {"n": 0}
sleeps = []


async def flaky():
    calls["n"] += 1
    if calls["n"] == 1:
        raise LLMProviderError("temporary", transient=True)
    return "ok"


res = run(
    with_retry(flaky, max_retries=3, base_delay=0.1, max_delay=1.0, sleep=make_sleep(sleeps))
)
check(
    "retry: succeeds after one transient failure",
    res == "ok" and calls["n"] == 2 and len(sleeps) == 1,
    detail=f"calls={calls['n']} sleeps={sleeps}",
)

# Exhausts retries then re-raises.
calls2 = {"n": 0}
sleeps2 = []


async def always_transient():
    calls2["n"] += 1
    raise LLMRateLimitError()


expect_raises(
    "retry: re-raises after exhausting retries",
    LLMRateLimitError,
    lambda: run(
        with_retry(
            always_transient,
            max_retries=2,
            base_delay=0.1,
            max_delay=1.0,
            sleep=make_sleep(sleeps2),
        )
    ),
)
check(
    "retry: attempted max_retries+1 times",
    calls2["n"] == 3,
    detail=f"calls={calls2['n']}",
)
check("retry: slept max_retries times", len(sleeps2) == 2, detail=f"sleeps={sleeps2}")

# Never retries a non-transient response error.
calls3 = {"n": 0}
sleeps3 = []


async def bad_response():
    calls3["n"] += 1
    raise LLMResponseError("bad json")


expect_raises(
    "retry: does NOT retry LLMResponseError",
    LLMResponseError,
    lambda: run(
        with_retry(
            bad_response, max_retries=3, base_delay=0.1, max_delay=1.0, sleep=make_sleep(sleeps3)
        )
    ),
)
check(
    "retry: response error attempted exactly once",
    calls3["n"] == 1 and len(sleeps3) == 0,
    detail=f"calls={calls3['n']} sleeps={sleeps3}",
)

# Never retries a non-transient provider error.
calls4 = {"n": 0}


async def permanent():
    calls4["n"] += 1
    raise LLMProviderError("4xx", transient=False)


expect_raises(
    "retry: does NOT retry non-transient provider error",
    LLMProviderError,
    lambda: run(
        with_retry(permanent, max_retries=3, base_delay=0.1, max_delay=1.0, sleep=make_sleep([]))
    ),
)
check("retry: non-transient attempted exactly once", calls4["n"] == 1)

# Backoff grows exponentially but is capped at max_delay.
sleeps5 = []


async def always_t():
    raise LLMProviderError("t", transient=True)


try:
    run(
        with_retry(
            always_t, max_retries=4, base_delay=1.0, max_delay=2.0, sleep=make_sleep(sleeps5)
        )
    )
except LLMProviderError:
    pass
check(
    "retry: exponential backoff capped at max_delay",
    sleeps5 == [1.0, 2.0, 2.0, 2.0],
    detail=f"sleeps={sleeps5}",
)


# ---------------------------------------------------------------------------
print("\n--- 7. OpenAIProvider (injected fake client, no network) ---")


def fake_response(content, model="gpt-4o-mini", pt=11, ct=7, tt=18, finish_reason=None):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
                finish_reason=finish_reason,
            )
        ],
        usage=SimpleNamespace(prompt_tokens=pt, completion_tokens=ct, total_tokens=tt),
        model=model,
    )


class FakeCompletions:
    def __init__(self, result=None, exc=None):
        self._result = result
        self._exc = exc
        self.calls = 0
        self.last_kwargs = None

    async def create(self, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        if self._exc is not None:
            raise self._exc
        return self._result


class FakeClient:
    def __init__(self, result=None, exc=None):
        self.chat = SimpleNamespace(completions=FakeCompletions(result=result, exc=exc))


settings = LLMSettings()

# --- success normalization ---
prov = OpenAIProvider(
    settings=settings,
    client=FakeClient(result=fake_response(json.dumps({"name": "proj", "score": 0.8}),
                                           model="gpt-4o-mini-2024")),
)
comp = run(
    prov.complete_structured(
        system_prompt="system", user_content="user", response_schema=_Sample
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
    comp.provider == "openai" and comp.model == "gpt-4o-mini-2024",
    detail=f"{comp.provider}/{comp.model}",
)
check(
    "provider: usage tokens normalized",
    comp.usage.prompt_tokens == 11
    and comp.usage.completion_tokens == 7
    and comp.usage.total_tokens == 18,
)
check(
    "provider: LLMUsage carries provider + model",
    comp.usage.provider == "openai" and comp.usage.model == "gpt-4o-mini-2024",
)

sent = prov._client.chat.completions.last_kwargs
check(
    "provider: requested response_format json_object",
    sent.get("response_format") == {"type": "json_object"},
    detail=repr(sent.get("response_format")),
)
check(
    "provider: sent system then user messages",
    [m["role"] for m in sent["messages"]] == ["system", "user"],
    detail=repr([m.get("role") for m in sent["messages"]]),
)

# --- non-JSON model output -> LLMResponseError ---
prov_bad = OpenAIProvider(settings=settings, client=FakeClient(result=fake_response("not-json")))
expect_raises(
    "provider: non-JSON content -> LLMResponseError",
    LLMResponseError,
    lambda: run(
        prov_bad.complete_structured(
            system_prompt="s", user_content="u", response_schema=_Sample
        )
    ),
)

# --- error mapping via the SDK's own exception types ---
import httpx  # noqa: E402  (test-only dependency, pulled in by openai)
from openai import (  # noqa: E402
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)

req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
resp429 = httpx.Response(429, request=req)

# Direct unit checks on the mapper.
check(
    "_map_openai_exception: APITimeoutError -> LLMTimeoutError",
    isinstance(_map_openai_exception(APITimeoutError(request=req)), LLMTimeoutError),
)
check(
    "_map_openai_exception: RateLimitError -> LLMRateLimitError",
    isinstance(
        _map_openai_exception(RateLimitError("rl", response=resp429, body=None)),
        LLMRateLimitError,
    ),
)
check(
    "_map_openai_exception: APIConnectionError -> transient LLMProviderError",
    _map_openai_exception(APIConnectionError(request=req)).transient is True,
)


def raising_provider(exc):
    return OpenAIProvider(settings=settings, client=FakeClient(exc=exc))


expect_raises(
    "provider: APITimeoutError -> LLMTimeoutError",
    LLMTimeoutError,
    lambda: run(
        raising_provider(APITimeoutError(request=req)).complete_structured(
            system_prompt="s", user_content="u", response_schema=_Sample
        )
    ),
)
expect_raises(
    "provider: RateLimitError -> LLMRateLimitError",
    LLMRateLimitError,
    lambda: run(
        raising_provider(
            RateLimitError("rl", response=resp429, body=None)
        ).complete_structured(system_prompt="s", user_content="u", response_schema=_Sample)
    ),
)
expect_raises(
    "provider: APIConnectionError -> LLMProviderError",
    LLMProviderError,
    lambda: run(
        raising_provider(APIConnectionError(request=req)).complete_structured(
            system_prompt="s", user_content="u", response_schema=_Sample
        )
    ),
)


def status_transient(code):
    resp = httpx.Response(code, request=req)
    provider = raising_provider(APIStatusError("e", response=resp, body=None))
    try:
        run(
            provider.complete_structured(
                system_prompt="s", user_content="u", response_schema=_Sample
            )
        )
    except LLMProviderError as exc:
        return exc.transient
    return "no-raise"


check("provider: HTTP 5xx -> transient LLMProviderError", status_transient(503) is True)
check("provider: HTTP 4xx -> non-transient LLMProviderError", status_transient(400) is False)

# --- missing API key -> LLMConfigurationError (deterministic) ---
saved_key = os.environ.pop("OPENAI_API_KEY", None)
try:
    expect_raises(
        "provider: missing OPENAI_API_KEY -> LLMConfigurationError",
        LLMConfigurationError,
        lambda: OpenAIProvider(settings=settings),
    )
finally:
    if saved_key is not None:
        os.environ["OPENAI_API_KEY"] = saved_key

# --- OpenAI-compatible gateway (OPENAI_BASE_URL) support ---
# These construct a REAL AsyncOpenAI client. Construction is offline (no network
# call happens until a request is made), so we can assert on the client's
# resolved base_url without a key or a live endpoint. api_key is passed
# explicitly so no real OPENAI_API_KEY is required.
_GATEWAY_URL = "https://gateway.example.com/v1"

# (a) explicit base_url arg routes the client at the gateway.
prov_gw = OpenAIProvider(settings=settings, api_key="test-key", base_url=_GATEWAY_URL)
check(
    "provider: explicit base_url routes client to the gateway",
    "gateway.example.com" in str(prov_gw._client.base_url),
    detail=str(prov_gw._client.base_url),
)

saved_base = os.environ.pop("OPENAI_BASE_URL", None)
try:
    # (b) OPENAI_BASE_URL env var is honored when no arg is passed.
    os.environ["OPENAI_BASE_URL"] = _GATEWAY_URL
    prov_env = OpenAIProvider(settings=settings, api_key="test-key")
    check(
        "provider: OPENAI_BASE_URL env routes client to the gateway",
        "gateway.example.com" in str(prov_env._client.base_url),
        detail=str(prov_env._client.base_url),
    )

    # (c) explicit arg overrides the env var.
    prov_override = OpenAIProvider(
        settings=settings, api_key="test-key", base_url="https://other.example.com/v1"
    )
    check(
        "provider: explicit base_url arg overrides OPENAI_BASE_URL env",
        "other.example.com" in str(prov_override._client.base_url),
        detail=str(prov_override._client.base_url),
    )

    # (d) blank env var is treated as unset -> default OpenAI endpoint.
    os.environ["OPENAI_BASE_URL"] = "   "
    prov_blank = OpenAIProvider(settings=settings, api_key="test-key")
    check(
        "provider: blank OPENAI_BASE_URL falls back to default OpenAI endpoint",
        "api.openai.com" in str(prov_blank._client.base_url),
        detail=str(prov_blank._client.base_url),
    )

    # (e) no base_url anywhere -> default OpenAI endpoint (backward compatible).
    os.environ.pop("OPENAI_BASE_URL", None)
    prov_default = OpenAIProvider(settings=settings, api_key="test-key")
    check(
        "provider: no base_url -> default OpenAI endpoint (backward compatible)",
        "api.openai.com" in str(prov_default._client.base_url),
        detail=str(prov_default._client.base_url),
    )
finally:
    os.environ.pop("OPENAI_BASE_URL", None)
    if saved_base is not None:
        os.environ["OPENAI_BASE_URL"] = saved_base


# ---------------------------------------------------------------------------
print("\n--- 7b. Truncation detection (finish_reason / MAX_TOKENS) ---")

# A response cut off at the output cap is deliberately NOT raised on and NOT
# retried: this layer requests temperature=0, so a second call would truncate at
# the identical point. The provider warns loudly and lets validate_response
# salvage the complete prefix into a partial-but-useful report.
prov_cut = OpenAIProvider(
    settings=settings,
    client=FakeClient(
        result=fake_response(
            '{"name": "proj", "score": 0.8, "notes": "cut mid-sent',
            finish_reason="length",
            ct=8000,
            tt=8011,
        )
    ),
)
cut_comp = run(
    prov_cut.complete_structured(
        system_prompt="s", user_content="u", response_schema=_Sample, max_tokens=8000
    )
)
check(
    "provider: finish_reason='length' yields a salvaged partial, not an error",
    isinstance(cut_comp, LLMCompletion)
    and isinstance(cut_comp.parsed, _Sample)
    and cut_comp.parsed.name == "proj"
    and cut_comp.parsed.score == 0.8,
)
check(
    "provider: truncated completion still reports its token usage",
    cut_comp.usage.completion_tokens == 8000,
    detail=str(cut_comp.usage.completion_tokens),
)
check(
    "provider: raw_text preserves the text exactly as received",
    cut_comp.raw_text.endswith('"cut mid-sent'),
    detail=repr(cut_comp.raw_text[-20:]),
)

cut_warnings = captured_warnings(
    "app.services.llm.openai_provider",
    lambda: run(
        prov_cut.complete_structured(
            system_prompt="s", user_content="u", response_schema=_Sample, max_tokens=8000
        )
    ),
)
check(
    "provider: truncation warns, naming the cap and the completion tokens",
    any("output-token cap" in m and "8000" in m for m in cut_warnings),
    detail=repr(cut_warnings),
)

prov_whole = OpenAIProvider(
    settings=settings,
    client=FakeClient(
        result=fake_response(json.dumps({"name": "p", "score": 0.1}), finish_reason="stop")
    ),
)
whole_warnings = captured_warnings(
    "app.services.llm.openai_provider",
    lambda: run(
        prov_whole.complete_structured(
            system_prompt="s", user_content="u", response_schema=_Sample
        )
    ),
)
check(
    "provider: finish_reason='stop' logs no truncation warning",
    not any("output-token cap" in m for m in whole_warnings),
    detail=repr(whole_warnings),
)

# --- Gemini reports the same condition as an SDK enum ---
from google.genai import types as genai_types  # noqa: E402  (declared dependency)

from app.services.llm.gemini_provider import _hit_token_cap  # noqa: E402


def gemini_response(*finish_reasons):
    return SimpleNamespace(
        candidates=[SimpleNamespace(finish_reason=r) for r in finish_reasons]
    )


check(
    "_hit_token_cap: SDK enum MAX_TOKENS -> True",
    _hit_token_cap(gemini_response(genai_types.FinishReason.MAX_TOKENS)) is True,
)
check(
    "_hit_token_cap: plain-string finish reason -> True",
    _hit_token_cap(gemini_response("FinishReason.MAX_TOKENS")) is True,
)
check(
    "_hit_token_cap: STOP -> False",
    _hit_token_cap(gemini_response(genai_types.FinishReason.STOP)) is False,
)
check(
    "_hit_token_cap: one truncated candidate among several -> True",
    _hit_token_cap(
        gemini_response(genai_types.FinishReason.STOP, genai_types.FinishReason.MAX_TOKENS)
    )
    is True,
)
check(
    "_hit_token_cap: empty candidates -> False",
    _hit_token_cap(SimpleNamespace(candidates=[])) is False,
)
check(
    "_hit_token_cap: response without candidates attr -> False",
    _hit_token_cap(SimpleNamespace()) is False,
)
check(
    "_hit_token_cap: None finish_reason -> False",
    _hit_token_cap(gemini_response(None)) is False,
)


# ---------------------------------------------------------------------------
print("\n--- 8. get_llm_provider factory ---")

expect_raises(
    "factory: unknown provider -> LLMConfigurationError",
    LLMConfigurationError,
    lambda: get_llm_provider("acme"),
)
saved_key = os.environ.pop("OPENAI_API_KEY", None)
try:
    expect_raises(
        "factory: openai routes to OpenAIProvider (no key -> LLMConfigurationError)",
        LLMConfigurationError,
        lambda: get_llm_provider("openai"),
    )
finally:
    if saved_key is not None:
        os.environ["OPENAI_API_KEY"] = saved_key


# ---------------------------------------------------------------------------
print("\n--- 9. LLMService.analyze end-to-end (fake provider) ---")

svc_tmp = tempfile.mkdtemp()
with open(os.path.join(svc_tmp, "widget_analysis.txt"), "w", encoding="utf-8") as fh:
    fh.write('Analyze for {schema_name}. JSON only: {{"ok": true}}')
svc_pm = PromptManager(prompts_dir=svc_tmp)


class FakeProvider(BaseLLMProvider):
    def __init__(self):
        self.last = None

    async def complete_structured(
        self,
        *,
        system_prompt,
        user_content,
        response_schema,
        model=None,
        temperature=0.0,
        max_tokens=None,
        timeout=None,
    ):
        self.last = SimpleNamespace(
            system_prompt=system_prompt,
            user_content=user_content,
            response_schema=response_schema,
            model=model,
        )
        parsed = response_schema.model_validate({"name": "x", "score": 0.42})
        usage = LLMUsage(
            provider="fakeprov",
            model="fake-model-1",
            prompt_tokens=5,
            completion_tokens=3,
            total_tokens=8,
        )
        return LLMCompletion(
            parsed=parsed,
            raw_text='{"name": "x", "score": 0.42}',
            usage=usage,
            provider="fakeprov",
            model="fake-model-1",
        )


fake_provider = FakeProvider()
service = LLMService(provider=fake_provider, prompt_manager=svc_pm, settings=LLMSettings())
check("service: constructed with injected provider (no API key needed)", True)

result = run(
    service.analyze(analyzer="widget", data={"projects": ["A"]}, response_schema=_Sample)
)
check(
    "service: returns validated schema instance",
    isinstance(result, _Sample) and result.score == 0.42,
)
check(
    "service: rendered system prompt used schema_name + unescaped braces",
    "Analyze for _Sample" in fake_provider.last.system_prompt
    and '{"ok": true}' in fake_provider.last.system_prompt,
    detail=repr(fake_provider.last.system_prompt),
)
check(
    "service: user_content is JSON-encoded data",
    json.loads(fake_provider.last.user_content) == {"projects": ["A"]},
)

rec = service.usage_tracker.records[-1]
check("service: usage record analyzer", rec.analyzer == "widget")
check("service: usage record schema_name", rec.schema_name == "_Sample")
check(
    "service: usage record provider + model from completion",
    rec.provider == "fakeprov" and rec.model == "fake-model-1",
)
check(
    "service: usage record tokens",
    rec.prompt_tokens == 5 and rec.completion_tokens == 3 and rec.total_tokens == 8,
)

# Missing prompt propagates as PromptNotFoundError.
expect_raises(
    "service: unknown prompt -> PromptNotFoundError",
    PromptNotFoundError,
    lambda: run(service.analyze(analyzer="ghost", data={}, response_schema=_Sample)),
)


# Service transparently retries a transient provider error (retry + service).
class FlakyProvider(BaseLLMProvider):
    def __init__(self):
        self.calls = 0

    async def complete_structured(self, *, response_schema, **_kw):
        self.calls += 1
        if self.calls == 1:
            raise LLMProviderError("temporary", transient=True)
        parsed = response_schema.model_validate({"name": "y", "score": 1.0})
        return LLMCompletion(
            parsed=parsed,
            raw_text="{}",
            usage=LLMUsage(
                provider="fp", model="m", prompt_tokens=1, completion_tokens=1, total_tokens=2
            ),
            provider="fp",
            model="m",
        )


flaky_provider = FlakyProvider()
fast_settings = LLMSettings(retry_base_delay=0.0, retry_max_delay=0.0, max_retries=2)
service2 = LLMService(provider=flaky_provider, prompt_manager=svc_pm, settings=fast_settings)
res2 = run(service2.analyze(analyzer="widget", data={}, response_schema=_Sample))
check(
    "service: transparently retries a transient provider error",
    isinstance(res2, _Sample) and flaky_provider.calls == 2,
    detail=f"calls={flaky_provider.calls}",
)


# ---------------------------------------------------------------------------
print("\n--- 10. UsageTracker cost estimation ---")

known = estimate_cost("gpt-4o-mini", 1000, 1000)
check("estimate_cost: known model returns positive cost", known is not None and known > 0)
check("estimate_cost: unknown model returns None", estimate_cost("mystery", 100, 100) is None)

tracker = UsageTracker()
tracker.record(
    analyzer="project",
    schema_name="StructuredAnalysis",
    provider="openai",
    model="gpt-4o-mini",
    prompt_tokens=100,
    completion_tokens=50,
    total_tokens=150,
)
check("UsageTracker.record appends a record", len(tracker.records) == 1)
check(
    "UsageTracker record fields populated",
    tracker.records[0].analyzer == "project"
    and tracker.records[0].total_tokens == 150,
)


# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if errors:
    print(f"FAILURES ({len(errors)}):")
    for item in errors:
        print(f"  - {item}")
    print("=" * 60)
    sys.exit(1)
else:
    print("ALL PHASE 3.6 LLM INTEGRATION TESTS PASSED")
    print("=" * 60)
    sys.exit(0)
