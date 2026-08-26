"""
app/analysis/engines/internship_analysis_engine.py
--------------------------------------------------
The SkillFit Internship Analysis Engine (Phase 3.8).

Orchestrates the evidence-based, per-internship intelligence pipeline.
This matches the exact architecture, rules, retry/truncation-recovery, and token 
efficiency mechanisms introduced in Phase 3.7.

Key contracts:
    - Provider-agnostic model.
    - Compact wire, full report. (Uses integer line-number references).
    - Resilience (per-internship failures are skipped).
    - No persistence (Phase 3.8 only generates analysis).
"""

import asyncio
import logging
import os
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple

from app.analysis.models.base import AnalysisEvidence
from app.analysis.models.internship_models import (
    AssessedPoint,
    Competency,
    ExecutiveAssessment,
    InternshipAnalysisResult,
    InternshipEvidence,
    InternshipIntelligenceReport,
    InternshipUnderstanding,
    MissingEvidenceItem,
    OwnershipClassification,
    SKILL_CLAIMED,
    SKILL_DEMONSTRATED,
    SKILL_UNVERIFIED,
    SKILL_VERIFIED,
    ScoredDimension,
    SkillEvidenceItem,
    SkillEvidenceMap,
    TechnologyUsage,
    WorkplaceMaturity,
)
from app.analysis.engines.internship_schemas import (
    AssessedPointSchema,
    CompetencySchema,
    EvidenceRef,
    ExecutiveAssessmentSchema,
    InternshipIntelligence,
    InternshipUnderstandingSchema,
    MissingEvidenceItemSchema,
    OwnershipClassificationSchema,
    ScoredDimensionSchema,
    SkillTechSchema,
    WorkplaceMaturitySchema,
)
from app.services.llm.exceptions import LLMError
from app.services.llm.service import LLMService, get_llm_service

logger = logging.getLogger(__name__)

DEFAULT_ANALYSIS_MAX_TOKENS: int = 8000
ANALYZER_NAME: str = "internship"
_EVIDENCE_SECTION: str = "internships"
_MAX_SCORE: float = 100.0

_BAND_VERIFIED: float = 0.75
_BAND_LIKELY: float = 0.40

_STATUS_TO_LIST: Dict[str, str] = {
    SKILL_CLAIMED: "claimed",
    SKILL_DEMONSTRATED: "demonstrated",
    SKILL_VERIFIED: "verified",
    SKILL_UNVERIFIED: "unverified",
}

_KIND_TECH = frozenset({"tech", "technology", "technologies"})
_KIND_SKILL = frozenset({"skill", "skills", "competency"})
_BULLET_CHARS: str = " \t-–—*+•·‣▪>"


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
            logger.warning("LLM_MAX_TOKENS=%r is not positive; using default %d.", env_value, DEFAULT_ANALYSIS_MAX_TOKENS)
        except ValueError:
            logger.warning("LLM_MAX_TOKENS=%r is not an integer; using default %d.", env_value, DEFAULT_ANALYSIS_MAX_TOKENS)
    return DEFAULT_ANALYSIS_MAX_TOKENS


def _confidence_band(confidence: float) -> str:
    if confidence <= 0.0:
        return "cannot_verify"
    if confidence >= _BAND_VERIFIED:
        return "verified"
    if confidence >= _BAND_LIKELY:
        return "likely"
    return "uncertain"


def _normalize_name(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


class InternshipAnalysisEngine:
    """
    Evidence-based internship analysis orchestrator.
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

    # -- public API ---------------------------------------------------------

    async def analyze_async(
        self, *, resume_id: str, internships: List[InternshipEvidence]
    ) -> InternshipAnalysisResult:
        """
        Analyze each internship from the extracted list.
        """
        result = InternshipAnalysisResult(
            internships=internships,
            total_internships_count=len(internships)
        )
        if not result.internships:
            logger.info("Internship analysis: no internships provided for resume %s; skipping LLM.", resume_id)
            return result

        llm = self._get_llm_service()
        logger.info(
            "Internship analysis: analyzing %d internship(s) for resume %s (max_tokens=%d).",
            len(result.internships), resume_id, self._max_tokens,
        )

        usage_offset = len(llm.usage_tracker.records)

        reports = await asyncio.gather(
            *(self._analyze_one(index, internship, llm)
              for index, internship in enumerate(result.internships))
        )
        result.reports = [report for report in reports if report is not None]

        self._log_output_cost(llm, usage_offset, resume_id)
        logger.info(
            "Internship analysis complete for resume %s: %d/%d report(s) generated.",
            resume_id, len(result.reports), len(result.internships),
        )
        return result

    def analyze(self, *, resume_id: str, internships: List[InternshipEvidence]) -> InternshipAnalysisResult:
        """
        Synchronous wrapper around analyze_async.
        """
        return asyncio.run(self.analyze_async(resume_id=resume_id, internships=internships))

    # -- internals ----------------------------------------------------------

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
            completion = sum(record.completion_tokens for record in batch)
            prompt = sum(record.prompt_tokens for record in batch)
            logger.info(
                "Internship analysis token cost for resume %s: %d call(s), "
                "%d prompt + %d completion tokens (mean %d completion/internship).",
                resume_id, len(batch), prompt, completion, completion // len(batch),
            )
        except Exception:
            logger.debug("Internship analysis: could not summarize token usage.", exc_info=True)

    async def _analyze_one(
        self, index: int, internship: InternshipEvidence, llm: LLMService
    ) -> Optional[InternshipIntelligenceReport]:
        payload = self._build_payload(internship)
        try:
            parsed = await llm.analyze(
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
                index, internship.role, type(exc).__name__, exc,
            )
            return None
        except Exception as exc:
            logger.error(
                "Internship analysis: unexpected error on internship #%d (%s) — %s: %s",
                index, internship.role, type(exc).__name__, exc,
            )
            return None

    # -- payload construction ----------------------------------------------

    @staticmethod
    def _build_payload(internship: InternshipEvidence) -> Dict[str, Any]:
        evidence: List[Dict[str, Any]] = []
        highlight_lines: List[int] = []
        highlights = {h.strip() for h in internship.achievements if h and h.strip()}

        for ev in internship.evidences:
            text = (ev.evidence_text or "").strip()
            entry: Dict[str, Any] = {
                "line": ev.line_number,
                "text": ev.evidence_text,
            }
            context = (ev.context_snippet or "").strip()
            if _context_adds_signal(text, context):
                entry["context"] = context
            evidence.append(entry)

            if ev.line_number is not None and text in highlights:
                highlight_lines.append(ev.line_number)

        payload: Dict[str, Any] = {
            "organization": internship.organization,
            "role": internship.role,
            "technologies": list(internship.technologies_used),
            "extraction_confidence": internship.confidence,
            "evidence": evidence,
        }
        if internship.duration:
            payload["duration"] = internship.duration
        if highlight_lines:
            payload["highlight_lines"] = highlight_lines
        return payload

    # -- evidence rehydration ----------------------------------------------

    @staticmethod
    def _build_line_index(internship: InternshipEvidence) -> Dict[int, AnalysisEvidence]:
        index: Dict[int, AnalysisEvidence] = {}
        for ev in internship.evidences:
            if ev.line_number is not None and ev.line_number not in index:
                index[ev.line_number] = ev
        return index

    def _resolve_refs(
        self,
        refs: Sequence[EvidenceRef],
        index: Dict[int, AnalysisEvidence],
        fallback_confidence: float,
    ) -> List[AnalysisEvidence]:
        resolved: List[AnalysisEvidence] = []
        seen: Set[EvidenceRef] = set()

        for ref in refs:
            if isinstance(ref, int):
                source = index.get(ref)
                if source is None:
                    continue
                if ref in seen:
                    continue
                seen.add(ref)
                resolved.append(
                    AnalysisEvidence(
                        evidence_text=source.evidence_text,
                        source_section=source.source_section or _EVIDENCE_SECTION,
                        confidence=source.confidence,
                        context_snippet=source.context_snippet,
                        line_number=source.line_number,
                    )
                )
                continue

            text = ref.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            resolved.append(
                AnalysisEvidence(
                    evidence_text=text,
                    source_section=_EVIDENCE_SECTION,
                    confidence=fallback_confidence,
                )
            )
        return resolved

    # -- Pydantic -> dataclass mapping -------------------------------------

    def _map_report(
        self, internship: InternshipEvidence, parsed: InternshipIntelligence
    ) -> InternshipIntelligenceReport:
        index = self._build_line_index(internship)

        technology_usage, skill_evidence = self._fan_out_skills_and_tech(
            parsed.skills_and_tech, internship.technologies_used, index
        )

        return InternshipIntelligenceReport(
            internship_role=internship.role,
            internship_organization=internship.organization,
            source_internship=internship,
            understanding=self._understanding(parsed.understanding, index),
            technical_depth=self._scored(parsed.technical_depth, "technical_depth", index),
            engineering_ownership=self._ownership(parsed.engineering_ownership, index),
            collaboration_exposure=self._scored(parsed.collaboration_exposure, "collaboration_exposure", index),
            impact_analysis=self._scored(parsed.impact_analysis, "impact_analysis", index),
            production_exposure=self._scored(parsed.production_exposure, "production_exposure", index),
            software_engineering_practices=self._scored(parsed.software_engineering_practices, "software_engineering_practices", index),
            technology_usage=technology_usage,
            competencies=[self._competency(c, index) for c in parsed.competencies],
            skill_evidence=skill_evidence,
            industry_readiness=self._scored(parsed.industry_readiness, "industry_readiness", index),
            hiring_signal=self._scored(parsed.hiring_signal, "hiring_signal", index),
            internship_quality=parsed.internship_quality or "",
            workplace_maturity=self._maturity(parsed.workplace_maturity, index),
            strengths=[self._point(p, index) for p in parsed.strengths],
            weaknesses=[self._point(p, index) for p in parsed.weaknesses],
            missing_evidence=[
                MissingEvidenceItem(
                    aspect=m.aspect or "",
                    description=m.description or "",
                    impact=m.impact or "",
                )
                for m in parsed.missing_evidence
            ],
            risks=[self._point(p, index) for p in parsed.risks],
            executive_assessment=self._executive(parsed.executive_assessment),
            overall_confidence=parsed.overall_confidence,
            overall_confidence_level=_confidence_band(parsed.overall_confidence),
            caveats=list(parsed.caveats),
        )

    # -- skills / technology fan-out ---------------------------------------

    @staticmethod
    def _is_technology(entry: SkillTechSchema, tech_lookup: FrozenSet[str]) -> bool:
        kind = (entry.kind or "").strip().lower()
        if kind in _KIND_TECH:
            return True
        if kind in _KIND_SKILL:
            return False
        if tech_lookup:
            return _normalize_name(entry.name or "") in tech_lookup
        return entry.depth > 0

    def _fan_out_skills_and_tech(
        self,
        entries: Iterable[SkillTechSchema],
        technologies: Sequence[str],
        index: Dict[int, AnalysisEvidence],
    ) -> Tuple[List[TechnologyUsage], SkillEvidenceMap]:
        tech_lookup = frozenset(
            _normalize_name(t) for t in technologies if t and t.strip()
        )

        technology_usage: List[TechnologyUsage] = []
        items: List[SkillEvidenceItem] = []
        grouped: Dict[str, List[str]] = {name: [] for name in _STATUS_TO_LIST.values()}

        for entry in entries:
            name = (entry.name or "").strip()
            if not name:
                continue

            evidence = self._resolve_refs(entry.ev, index, entry.confidence)
            status = (entry.status or SKILL_UNVERIFIED).strip() or SKILL_UNVERIFIED

            items.append(
                SkillEvidenceItem(
                    skill=name,
                    status=status,
                    confidence=entry.confidence,
                    reasoning=entry.reasoning or "",
                    evidence=evidence,
                )
            )
            list_name = _STATUS_TO_LIST.get(status.lower())
            if list_name is not None:
                grouped[list_name].append(name)

            if self._is_technology(entry, tech_lookup):
                technology_usage.append(
                    TechnologyUsage(
                        technology=name,
                        usage_depth_score=entry.depth,
                        max_score=_MAX_SCORE,
                        sophistication=entry.sophistication or "",
                        demonstrated_understanding=entry.understanding or "",
                        confidence=entry.confidence,
                        confidence_level=_confidence_band(entry.confidence),
                        reasoning=entry.reasoning or "",
                        evidence=self._resolve_refs(entry.ev, index, entry.confidence),
                    )
                )

        skill_evidence = SkillEvidenceMap(
            claimed=grouped["claimed"],
            demonstrated=grouped["demonstrated"],
            verified=grouped["verified"],
            unverified=grouped["unverified"],
            items=items,
        )
        return technology_usage, skill_evidence

    # -- per-structure mappers ---------------------------------------------

    def _scored(
        self, sd: ScoredDimensionSchema, name: str, index: Dict[int, AnalysisEvidence]
    ) -> ScoredDimension:
        return ScoredDimension(
            name=name,
            score=sd.score,
            max_score=_MAX_SCORE,
            confidence=sd.confidence,
            confidence_level=_confidence_band(sd.confidence),
            reasoning=sd.reasoning or "",
            evidence=self._resolve_refs(sd.ev, index, sd.confidence),
        )

    def _understanding(
        self, u: InternshipUnderstandingSchema, index: Dict[int, AnalysisEvidence]
    ) -> InternshipUnderstanding:
        return InternshipUnderstanding(
            purpose=u.purpose or "",
            domain=u.domain or "",
            company_type=u.company_type or "",
            team_function=u.team_function or "",
            role_objective=u.role_objective or "",
            confidence=u.confidence,
            confidence_level=_confidence_band(u.confidence),
            evidence=self._resolve_refs(u.ev, index, u.confidence),
        )

    def _ownership(
        self, o: OwnershipClassificationSchema, index: Dict[int, AnalysisEvidence]
    ) -> OwnershipClassification:
        return OwnershipClassification(
            classification=o.classification or "",
            score=o.score,
            max_score=_MAX_SCORE,
            confidence=o.confidence,
            confidence_level=_confidence_band(o.confidence),
            reasoning=o.reasoning or "",
            evidence=self._resolve_refs(o.ev, index, o.confidence),
        )

    def _maturity(
        self, m: WorkplaceMaturitySchema, index: Dict[int, AnalysisEvidence]
    ) -> WorkplaceMaturity:
        return WorkplaceMaturity(
            classification=m.classification or "",
            score=m.score,
            max_score=_MAX_SCORE,
            confidence=m.confidence,
            confidence_level=_confidence_band(m.confidence),
            reasoning=m.reasoning or "",
            evidence=self._resolve_refs(m.ev, index, m.confidence),
        )

    def _competency(
        self, c: CompetencySchema, index: Dict[int, AnalysisEvidence]
    ) -> Competency:
        return Competency(
            name=c.name or "",
            score=c.score,
            max_score=_MAX_SCORE,
            confidence=c.confidence,
            confidence_level=_confidence_band(c.confidence),
            reasoning=c.reasoning or "",
            evidence=self._resolve_refs(c.ev, index, c.confidence),
        )

    def _point(
        self, p: AssessedPointSchema, index: Dict[int, AnalysisEvidence]
    ) -> AssessedPoint:
        return AssessedPoint(
            statement=p.statement or "",
            reasoning=p.reasoning or "",
            confidence=p.confidence,
            confidence_level=_confidence_band(p.confidence),
            evidence=self._resolve_refs(p.ev, index, p.confidence),
        )

    @staticmethod
    def _executive(ea: ExecutiveAssessmentSchema) -> ExecutiveAssessment:
        return ExecutiveAssessment(
            overall_impression=ea.overall_impression or "",
            demonstrates=list(ea.demonstrates),
            does_not_demonstrate=list(ea.does_not_demonstrate),
            strongest_signals=list(ea.strongest_signals),
            weakest_signals=list(ea.weakest_signals),
            overall_confidence=ea.overall_confidence,
            confidence_level=_confidence_band(ea.overall_confidence),
        )
