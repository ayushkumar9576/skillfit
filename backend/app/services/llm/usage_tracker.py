"""
app/services/llm/usage_tracker.py
---------------------------------
Usage / cost tracking for the SkillFit LLM Integration Layer (Phase 3.6).

Per the Phase 3.6 scope, this does NOT introduce a database table or Alembic
migration. Usage is captured behind a small ``UsageTracker`` interface that:

    - emits a privacy-safe structured log line per call (token counts and
      metadata ONLY — never prompt content or model output), and
    - keeps an in-memory list of records for inspection and tests.

A DB-backed sink can be added later (Phase 3.12) without changing callers.

Each record carries enough metadata — ``analyzer`` (which engine issued the
request), ``schema_name`` (which response schema it expected), plus
``provider`` and ``model`` — to debug issues, monitor token usage, and compare
cost/performance across analyzers in future phases.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Indicative USD price per 1,000 tokens as (prompt, completion). Values are
# approximate and only used for a best-effort cost estimate; unknown models
# yield a graceful ``None`` estimate rather than an error.
_PRICE_PER_1K_TOKENS: Dict[str, Tuple[float, float]] = {
    "gpt-4o-mini": (0.00015, 0.00060),
    "gpt-4o": (0.00500, 0.01500),
}


def estimate_cost(
    model: str, prompt_tokens: int, completion_tokens: int
) -> Optional[float]:
    """
    Best-effort USD cost estimate for a completion.

    Returns:
        Rounded USD estimate, or ``None`` if the model's pricing is unknown.
    """
    price = _PRICE_PER_1K_TOKENS.get(model)
    if price is None:
        return None
    prompt_price, completion_price = price
    cost = (prompt_tokens / 1000.0) * prompt_price + (
        completion_tokens / 1000.0
    ) * completion_price
    return round(cost, 6)


@dataclass
class LLMUsageRecord:
    """
    One recorded LLM call. Pure stdlib dataclass (no framework deps), matching
    the style of ``app/analysis/models/base.py``.
    """

    analyzer: str
    schema_name: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: Optional[float]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class UsageTracker:
    """
    Collects :class:`LLMUsageRecord` entries.

    The default implementation logs each record and retains it in memory.
    Subclass and override :meth:`record` to add a DB or metrics sink later.
    """

    def __init__(self) -> None:
        self._records: List[LLMUsageRecord] = []

    def record(
        self,
        *,
        analyzer: str,
        schema_name: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
    ) -> LLMUsageRecord:
        """
        Record a single LLM call. Logs a privacy-safe summary and stores the
        record in memory.

        Returns:
            The created :class:`LLMUsageRecord`.
        """
        estimated_cost = estimate_cost(model, prompt_tokens, completion_tokens)
        record = LLMUsageRecord(
            analyzer=analyzer,
            schema_name=schema_name,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost,
        )
        self._records.append(record)

        # Structured, privacy-safe log — metadata + token counts only.
        logger.info(
            "LLM usage: analyzer=%s schema=%s provider=%s model=%s "
            "prompt_tokens=%d completion_tokens=%d total_tokens=%d est_cost_usd=%s",
            analyzer,
            schema_name,
            provider,
            model,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            "unknown" if estimated_cost is None else f"{estimated_cost:.6f}",
        )
        return record

    @property
    def records(self) -> List[LLMUsageRecord]:
        """Return a shallow copy of the recorded usage entries."""
        return list(self._records)
