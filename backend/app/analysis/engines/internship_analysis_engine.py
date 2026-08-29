"""
app/analysis/engines/internship_analysis_engine.py
---------------------------------------------------
SkillFit Internship Analysis Engine — Phase 3 Remediation.

Orchestrates the per-internship intelligence pipeline.
Calls the LLM with the new InternshipIntelligence schema (qualitative, no scores)
and maps the result directly to CandidateIntelligenceProfile objects.

LLM infrastructure (provider, retry, token control, batch gather) unchanged.
Only the mapper layer has been replaced.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Sequence, Set

from app.analysis.models.candidate_profile import (
    CompetencyIntelligence,
    DemonstrationLevel,
    EngineeringSignal,
    EngineeringSignalCategory,
    Finding,
    IntelligenceEvidence,
    IntelligenceSourceType,
    OwnershipIntelligence,
    TechnologyIntelligence,
    WorkplaceExposure,
)
from app.analysis.engines.internship_schemas import (
    EvidenceRef,
    InternshipIntelligence,
)
from app.analysis.models.base import AnalysisEvidence
from app.services.llm.exceptions import LLMError
from app.services.llm.service import LLMService, get_llm_service

logger = logging.getLogger(__name__)

DEFAULT_ANALYSIS_MAX_TOKENS: int = 8000
ANALYZER_NAME: str = "internship"
_EVIDENCE_SECTION: str = "internships"
_BULLET_CHARS: str = " \t-\u2013\u2014*+\u2022\u00b7\u2023\u25aa>"

_VALID_DEMO_LEVELS: Set[str] = {d.value for d in DemonstrationLevel}
_VALID_ENG_CATEGORIES: Set[str] = {c.value for c in EngineeringSignalCategory}


def _context_adds_signal(text: str, context: str) -> bool:
    if not context:
        return False
    return context.lstrip(_BULLET_CHARS).strip() != text.lstrip(_BULLET_CHARS).strip()


def _resolve_max_tokens(explicit: Optional[int]) -> int:
    if explicit is not None:
        return explicit
    env_value = os.getenv("LLM_MAX_TOKENS")
    if env_value and env_value.strip():
        try:
            parsed = int(env_value.strip())
            if parsed > 0:
                return parsed
            logger.warning(
                "LLM_MAX_TOKENS=%r is not positive; using default %d.",
                env_value, DEFAULT_ANALYSIS_MAX_TOKENS,
            )
        except ValueError:
            logger.warning(
                "LLM_MAX_TOKENS=%r is not an integer; using default %d.",
                env_value, DEFAULT_ANALYSIS_MAX_TOKENS,
            )
    return DEFAULT_ANALYSIS_MAX_TOKENS


def _safe_demo_level(raw: Optional[str]) -> str:
    if raw and raw.upper() in _VALID_DEMO_LEVELS:
        return raw.upper()
    return DemonstrationLevel.CLAIMED.value


def _safe_eng_category(raw: Optional[str]) -> Optional[str]:
    if raw and raw.upper() in _VALID_ENG_CATEGORIES:
        return raw.upper()
    return None


# ---------------------------------------------------------------------------
# Internship evidence container (unchanged from extractor)
# ---------------------------------------------------------------------------

try:
    from app.services.resume.internship_extractor import InternshipEvidence
except ImportError:
    InternshipEvidence = Any  # type: ignore


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field


@dataclass
class InternshipAnalysisResult:
    """Container for all internship intelligence objects."""
    internships: List[Any] = field(default_factory=list)
    total_internships_count: int = 0
    technologies: List[TechnologyIntelligence] = field(default_factory=list)
    competencies: List[CompetencyIntelligence] = field(default_factory=list)
    ownership_signals: List[OwnershipIntelligence] = field(default_factory=list)
    workplace_exposure: List[WorkplaceExposure] = field(default_factory=list)
    engineering_signals: List[EngineeringSignal] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class InternshipAnalysisEngine:
    """
    Evidence-based internship analysis orchestrator — Phase 3 Remediation.

    Per-internship LLM call → InternshipIntelligence schema →
    candidate_profile objects (TechnologyIntelligence, CompetencyIntelligence,
    OwnershipIntelligence, WorkplaceExposure, EngineeringSignal, Finding).
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.0,
    ) -> None:
        self._llm_service = llm_service
        self._model = model
        self._max_tokens = _resolve_max_tokens(max_tokens)
        self._temperature = temperature

    async def analyze_async(
        self, *, resume_id: str, internships: List[Any]
    ) -> InternshipAnalysisResult:
        result = InternshipAnalysisResult(
            internships=internships,
            total_internships_count=len(internships),
        )
        if not internships:
            logger.info(
                "Internship analysis: no internships for resume %s; skipping.", resume_id
            )
            return result

        llm = self._get_llm_service()
        logger.info(
            "Internship analysis: analyzing %d internship(s) for resume %s (max_tokens=%d).",
            len(internships), resume_id, self._max_tokens,
        )

        usage_offset = len(llm.usage_tracker.records)
        per_internship = await asyncio.gather(
            *(self._analyze_one(idx, internship, llm, resume_id)
              for idx, internship in enumerate(internships))
        )
        self._log_output_cost(llm, usage_offset, resume_id)

        for intel in per_internship:
            if intel is None:
                continue
            result.technologies.extend(intel.get("technologies", []))
            result.competencies.extend(intel.get("competencies", []))
            result.ownership_signals.extend(intel.get("ownership_signals", []))
            result.workplace_exposure.extend(intel.get("workplace_exposure", []))
            result.engineering_signals.extend(intel.get("engineering_signals", []))
            result.findings.extend(intel.get("findings", []))

        logger.info(
            "Internship analysis complete for resume %s: %d/%d processed.",
            resume_id, sum(1 for i in per_internship if i), len(internships),
        )
        return result

    def analyze(self, *, resume_id: str, internships: List[Any]) -> InternshipAnalysisResult:
        return asyncio.run(self.analyze_async(resume_id=resume_id, internships=internships))

    def _get_llm_service(self) -> LLMService:
        if self._llm_service is None:
            self._llm_service = get_llm_service()
        return self._llm_service

    @staticmethod
    def _log_output_cost(llm: LLMService, offset: int, resume_id: str) -> None:
        try:
            batch = llm.usage_tracker.records[offset:]
            if not batch:
                return
            completion = sum(r.completion_tokens for r in batch)
            prompt = sum(r.prompt_tokens for r in batch)
            logger.info(
                "Internship token cost for resume %s: %d call(s), %d prompt + %d completion tokens.",
                resume_id, len(batch), prompt, completion,
            )
        except Exception:
            logger.debug("Could not summarize internship token usage.", exc_info=True)

    async def _analyze_one(
        self, index: int, internship: Any, llm: LLMService, resume_id: str
    ) -> Optional[Dict[str, Any]]:
        payload = self._build_payload(internship)
        try:
            parsed: InternshipIntelligence = await llm.analyze(
                analyzer=ANALYZER_NAME,
                data=payload,
                response_schema=InternshipIntelligence,
                model=self._model,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            return self._map_report(internship, parsed)
        except LLMError as exc:
            logger.warning(
                "Internship analysis: skipping internship #%d (%s) — %s: %s",
                index, getattr(internship, "role", "unknown"), type(exc).__name__, exc,
            )
            return None
        except Exception as exc:
            logger.error(
                "Internship analysis: unexpected error on internship #%d (%s) — %s",
                index, getattr(internship, "role", "unknown"), exc,
                exc_info=True,
            )
            return None

    # -- payload construction ------------------------------------------------

    @staticmethod
    def _build_payload(internship: Any) -> Dict[str, Any]:
        evidence: List[Dict[str, Any]] = []
        highlight_lines: List[int] = []
        highlights = {h.strip() for h in (getattr(internship, "achievements", []) or []) if h and h.strip()}

        for ev in (getattr(internship, "evidences", []) or []):
            text = (ev.evidence_text or "").strip()
            entry: Dict[str, Any] = {
                "line": ev.line_number,
                "text": ev.evidence_text,
            }
            context = (ev.context_snippet or "").strip()
            if context and context != text:
                entry["context"] = context
            evidence.append(entry)
            if ev.line_number is not None and text in highlights:
                highlight_lines.append(ev.line_number)

        payload: Dict[str, Any] = {
            "organization": getattr(internship, "organization", ""),
            "role": getattr(internship, "role", ""),
            "technologies": list(getattr(internship, "technologies_used", []) or []),
            "extraction_confidence": getattr(internship, "confidence", 0.0),
            "evidence": evidence,
        }
        if getattr(internship, "duration", None):
            payload["duration"] = internship.duration
        if highlight_lines:
            payload["highlight_lines"] = highlight_lines
        return payload

    # -- evidence rehydration ------------------------------------------------

    @staticmethod
    def _build_line_index(internship: Any) -> Dict[int, AnalysisEvidence]:
        index: Dict[int, AnalysisEvidence] = {}
        for ev in (getattr(internship, "evidences", []) or []):
            if ev.line_number is not None and ev.line_number not in index:
                index[ev.line_number] = ev
        return index

    def _resolve_refs(
        self,
        refs: Sequence[EvidenceRef],
        index: Dict[int, AnalysisEvidence],
        internship_id: str,
        section: str = _EVIDENCE_SECTION,
    ) -> List[IntelligenceEvidence]:
        """Convert line-number refs to IntelligenceEvidence objects."""
        resolved: List[IntelligenceEvidence] = []
        seen: Set[EvidenceRef] = set()
        for ref in refs:
            if isinstance(ref, int):
                source = index.get(ref)
                if source is None or ref in seen:
                    continue
                seen.add(ref)
                resolved.append(IntelligenceEvidence(
                    source=IntelligenceSourceType.INTERNSHIP,
                    source_id=internship_id,
                    section=section,
                    quote=(source.evidence_text or "").strip(),
                    line_reference=ref,
                ))
            else:
                text = str(ref).strip()
                if not text or text in seen:
                    continue
                seen.add(text)
                resolved.append(IntelligenceEvidence(
                    source=IntelligenceSourceType.INTERNSHIP,
                    source_id=internship_id,
                    section=section,
                    quote=text,
                ))
        return resolved

    # -- Mapper: InternshipIntelligence → candidate_profile objects ----------

    def _map_report(self, internship: Any, parsed: InternshipIntelligence) -> Dict[str, Any]:
        role = getattr(internship, "role", "") or ""
        org = getattr(internship, "organization", "") or ""
        internship_id = f"{org}|{role}".strip("|") or "internship"
        index = self._build_line_index(internship)

        # ── Technologies ───────────────────────────────────────────────────
        technologies: List[TechnologyIntelligence] = []
        for t in parsed.technologies:
            if not t.technology:
                continue
            evidence = self._resolve_refs(t.ev, index, internship_id)
            technologies.append(TechnologyIntelligence(
                technology=t.technology.strip(),
                demonstration_level=_safe_demo_level(t.demonstration_level),
                evidence=evidence,
                source_types=["internship"],
            ))

        # ── Competencies ───────────────────────────────────────────────────
        competencies: List[CompetencyIntelligence] = []
        for c in parsed.competencies:
            if not c.competency:
                continue
            evidence = self._resolve_refs(c.ev, index, internship_id)
            competencies.append(CompetencyIntelligence(
                competency=c.competency.upper().strip(),
                demonstrated=bool(c.demonstrated),
                demonstration_level=_safe_demo_level(c.demonstration_level),
                evidence=evidence,
                supporting_technologies=list(c.supporting_technologies or []),
                supporting_projects=[],
            ))

        # ── Ownership signals ──────────────────────────────────────────────
        ownership_signals: List[OwnershipIntelligence] = []
        for o in parsed.ownership_signals:
            if not o.signal:
                continue
            evidence = self._resolve_refs(o.ev, index, internship_id)
            ownership_signals.append(OwnershipIntelligence(
                signal=o.signal.strip(),
                ownership_level=(o.ownership_level or "CONTRIBUTED").upper(),
                evidence=evidence,
            ))

        # ── Workplace exposure ─────────────────────────────────────────────
        workplace_exposure: List[WorkplaceExposure] = []
        for w in parsed.workplace_exposure:
            if not w.exposure_type:
                continue
            evidence = self._resolve_refs(w.ev, index, internship_id)
            workplace_exposure.append(WorkplaceExposure(
                exposure_type=w.exposure_type.strip(),
                evidence=evidence,
            ))

        # ── Engineering signals ────────────────────────────────────────────
        engineering_signals: List[EngineeringSignal] = []
        for e in parsed.engineering_signals:
            category = _safe_eng_category(e.category)
            if not category or not e.signal:
                continue
            evidence = self._resolve_refs(e.ev, index, internship_id)
            engineering_signals.append(EngineeringSignal(
                category=category,
                signal=e.signal.strip(),
                demonstrated=bool(e.demonstrated),
                evidence=evidence,
            ))

        # ── Findings ───────────────────────────────────────────────────────
        findings: List[Finding] = []
        for f in parsed.findings:
            if not f.title or not f.type:
                continue
            evidence = self._resolve_refs(f.ev, index, internship_id)
            findings.append(Finding(
                type=(f.type or "").upper().strip(),
                severity=(f.severity or "MEDIUM").upper().strip(),
                title=f.title.strip(),
                description=(f.description or "").strip(),
                evidence=evidence,
            ))

        return {
            "technologies": technologies,
            "competencies": competencies,
            "ownership_signals": ownership_signals,
            "workplace_exposure": workplace_exposure,
            "engineering_signals": engineering_signals,
            "findings": findings,
        }
