"""
app/services/llm/retry.py
-------------------------
Async, transient-only retry with exponential backoff for the SkillFit LLM
Integration Layer (Phase 3.6).

Design:
    - **Async-native.** ``with_retry`` is an ``async def`` and ``await``s the
      supplied coroutine factory. There is NO ``asyncio.run`` here — the
      async→sync bridge lives only at the outer orchestration boundary
      (the test harness now; the pipeline stage in Phase 3.7+).
    - **Transient-only.** Only ``LLMProviderError`` instances whose
      ``.transient`` flag is ``True`` are retried. ``LLMResponseError``,
      ``PromptNotFoundError``, ``PromptRenderError``, and
      ``LLMConfigurationError`` are never retried — they propagate immediately.
    - **Injectable sleep.** ``sleep`` defaults to ``asyncio.sleep`` but can be
      replaced in tests so they never actually wait.
"""

import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

from app.services.llm.exceptions import LLMProviderError

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    max_retries: int,
    base_delay: float,
    max_delay: float,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> T:
    """
    Invoke ``fn()`` (a zero-arg coroutine factory), retrying on transient
    provider errors with exponential backoff.

    Total attempts = ``max_retries`` + 1 (one initial attempt plus up to
    ``max_retries`` retries).

    Args:
        fn:          Zero-argument callable returning a fresh awaitable each
                     call (e.g. ``lambda: provider.complete_structured(...)``).
        max_retries: Maximum number of *retries* after the first attempt.
        base_delay:  Base backoff delay in seconds (delay = base_delay * 2**attempt).
        max_delay:   Upper bound on any single backoff delay, in seconds.
        sleep:       Awaitable sleep function (injectable for tests).

    Returns:
        Whatever ``fn()`` resolves to on the first successful attempt.

    Raises:
        LLMProviderError: the last transient error, once retries are exhausted.
        Any non-transient / non-provider exception: propagated immediately.
    """
    attempt = 0
    while True:
        try:
            return await fn()
        except LLMProviderError as exc:
            # Non-transient failures, or exhausted retries → give up.
            if not exc.transient or attempt >= max_retries:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(
                "Transient LLM provider error on attempt %d/%d (%s). Retrying in %.2fs.",
                attempt + 1,
                max_retries + 1,
                type(exc).__name__,
                delay,
            )
            await sleep(delay)
            attempt += 1
