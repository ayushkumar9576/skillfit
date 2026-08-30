"""
app/analysis/engines/project_analysis_engine.py
------------------------------------------------
SkillFit Project Analysis Engine — Phase 3 Remediation.

Orchestrates the per-project intelligence pipeline.
Calls the LLM with the new ProjectIntelligence schema (qualitative, no scores)
and maps the result directly to CandidateIntelligenceProfile objects.

LLM infrastructure (provider, retry, token control) is unchanged.
Only the mapper layer (_map_report) has been replaced to produce
TechnologyIntelligence, CompetencyIntelligence, OwnershipIntelligence,
EngineeringSignal, and Finding objects from candidate_profile.py.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from app.analysis.models.candidate_profile import (
    CompetencyIntelligence,
    DemonstrationLevel,
    EngineeringSignal,
    EngineeringSignalCategory,
    Finding,
    IntelligenceEvidence,
    IntelligenceSourceType,
    OwnershipIntelligence,
    ProjectSophisticationRecord,
    TechnologyIntelligence,
)
from app.analysis.models.project_models import score_to_tier
from app.analysis.engines.project_schemas import (
    EvidenceRef,
    ProjectIntelligence,
    TechnologyIntelligenceSchema,
    CompetencyIntelligenceSchema,
    OwnershipSignalSchema,
    EngineeringSignalSchema,
    FindingSchema,
    UnderstandingSchema,
)
from app.analysis.models.base import AnalysisEvidence
from app.services.llm.exceptions import LLMError
from app.services.llm.service import LLMService, get_llm_service
from app.services.resume.project_extractor import (
    BaseProjectExtractor,
    get_project_extractor,
)

logger = logging.getLogger(__name__)

DEFAULT_ANALYSIS_MAX_TOKENS: int = 8000
ANALYZER_NAME: str = "project"
_EVIDENCE_SECTION: str = "projects"
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
        except ValueError:
            pass
    return DEFAULT_ANALYSIS_MAX_TOKENS


def _safe_demo_level(raw: Optional[str]) -> str:
    """Return a valid DemonstrationLevel value, defaulting to CLAIMED."""
    if raw and raw.upper() in _VALID_DEMO_LEVELS:
        return raw.upper()
    return DemonstrationLevel.CLAIMED.value


def _safe_eng_category(raw: Optional[str]) -> Optional[str]:
    """Return a valid EngineeringSignalCategory value, or None if unrecognized."""
    if raw and raw.upper() in _VALID_ENG_CATEGORIES:
        return raw.upper()
    return None


class ProjectAnalysisEngine:
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        extractor: Optional[BaseProjectExtractor] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.0,
    ) -> None:
        self._llm_service = llm_service
        self._extractor = extractor or get_project_extractor("rule_based")
        self._model = model
        self._max_tokens = _resolve_max_tokens(max_tokens)
        self._temperature = temperature

    async def analyze_async(
        self, *, resume_id: str, raw_text: str
    ) -> Dict[str, Any]:
        """
        Analyze all projects in raw_text.

        Returns a dict with keys:
            projects: list of ProjectEvidence (from extractor)
            technologies: List[TechnologyIntelligence]
            competencies: List[CompetencyIntelligence]
            ownership_signals: List[OwnershipIntelligence]
            engineering_signals: List[EngineeringSignal]
            findings: List[Finding]
        Aggregation into CandidateIntelligenceProfile is done by the pipeline.
        """
        result = self._extractor.extract(raw_text)
        if not result.projects:
            return self._empty_result()

        llm = self._get_llm_service()
        per_project = await asyncio.gather(
            *(self._analyze_one(index, project, llm, resume_id)
              for index, project in enumerate(result.projects))
        )
        return self._merge_results(per_project)

    def analyze(self, *, resume_id: str, raw_text: str) -> Dict[str, Any]:
        return asyncio.run(self.analyze_async(resume_id=resume_id, raw_text=raw_text))

    def _get_llm_service(self) -> LLMService:
        if self._llm_service is None:
            self._llm_service = get_llm_service()
        return self._llm_service

    @staticmethod
    def _empty_result() -> Dict[str, Any]:
        return {
            "technologies": [],
            "competencies": [],
            "ownership_signals": [],
            "engineering_signals": [],
            "findings": [],
            "project_sophistication": [],
        }

    @staticmethod
    def _merge_results(per_project: List[Optional[Dict[str, Any]]]) -> Dict[str, Any]:
        merged: Dict[str, List] = {
            "technologies": [],
            "competencies": [],
            "ownership_signals": [],
            "engineering_signals": [],
            "findings": [],
            "project_sophistication": [],
        }
        for result in per_project:
            if result is None:
                continue
            for key in merged:
                merged[key].extend(result.get(key, []))
        return merged

    async def _analyze_one(
        self, index: int, project: Any, llm: LLMService, resume_id: str
    ) -> Optional[Dict[str, Any]]:
        payload = self._build_payload(project)
        try:
            parsed: ProjectIntelligence = await llm.analyze(
                analyzer=ANALYZER_NAME,
                data=payload,
                response_schema=ProjectIntelligence,
                model=self._model,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            return self._map_report(project, parsed, resume_id)
        except Exception as exc:
            logger.error(
                "Project analysis failed for project #%d (%s) [resume %s]: %s",
                index, getattr(project, "title", "unknown"), resume_id, exc,
                exc_info=True,
            )
            return None

    @staticmethod
    def _build_payload(project: Any) -> Dict[str, Any]:
        evidence: List[Dict[str, Any]] = []
        highlight_lines: List[int] = []
        highlights = {h.strip() for h in project.highlights if h and h.strip()}

        for ev in project.evidences:
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
            "project_title": project.title,
            "technologies": list(project.technologies),
            "extraction_confidence": project.confidence,
            "evidence": evidence,
        }
        if project.role:
            payload["role"] = project.role
        if project.project_url:
            payload["project_url"] = project.project_url
        if highlight_lines:
            payload["highlight_lines"] = highlight_lines
        return payload

    @staticmethod
    def _build_line_index(project: Any) -> Dict[int, AnalysisEvidence]:
        index: Dict[int, AnalysisEvidence] = {}
        for ev in project.evidences:
            if ev.line_number is not None and ev.line_number not in index:
                index[ev.line_number] = ev
        return index

    def _resolve_refs(
        self,
        refs: Sequence[EvidenceRef],
        index: Dict[int, AnalysisEvidence],
        project_id: str,
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
                    source=IntelligenceSourceType.PROJECT,
                    source_id=project_id,
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
                    source=IntelligenceSourceType.PROJECT,
                    source_id=project_id,
                    section=section,
                    quote=text,
                ))
        return resolved

    def _map_report(
        self, project: Any, parsed: ProjectIntelligence, resume_id: str
    ) -> Dict[str, Any]:
        """
        Map ProjectIntelligence (LLM output) to candidate_profile objects.
        Returns a dict ready to be fed to CandidateIntelligenceAggregator.
        """
        project_id = getattr(project, "title", resume_id)
        index = self._build_line_index(project)

        # ── Technologies ───────────────────────────────────────────────────
        technologies: List[TechnologyIntelligence] = []
        for t in parsed.technologies:
            if not t.technology:
                continue
            evidence = self._resolve_refs(t.ev, index, project_id)
            technologies.append(TechnologyIntelligence(
                technology=t.technology.strip(),
                demonstration_level=_safe_demo_level(t.demonstration_level),
                evidence=evidence,
                source_types=["project"],
            ))

        # ── Competencies ───────────────────────────────────────────────────
        competencies: List[CompetencyIntelligence] = []
        for c in parsed.competencies:
            if not c.competency:
                continue
            evidence = self._resolve_refs(c.ev, index, project_id)
            comp = CompetencyIntelligence(
                competency=c.competency.upper().strip(),
                demonstrated=bool(c.demonstrated),
                demonstration_level=_safe_demo_level(c.demonstration_level),
                evidence=evidence,
                supporting_technologies=list(c.supporting_technologies or []),
                supporting_projects=[project_id],
            )
            competencies.append(comp)

        # ── Ownership signals ──────────────────────────────────────────────
        ownership_signals: List[OwnershipIntelligence] = []
        for o in parsed.ownership_signals:
            if not o.signal:
                continue
            evidence = self._resolve_refs(o.ev, index, project_id)
            ownership_signals.append(OwnershipIntelligence(
                signal=o.signal.strip(),
                ownership_level=(o.ownership_level or "CONTRIBUTED").upper(),
                evidence=evidence,
            ))

        # ── Engineering signals ────────────────────────────────────────────
        engineering_signals: List[EngineeringSignal] = []
        for e in parsed.engineering_signals:
            category = _safe_eng_category(e.category)
            if not category or not e.signal:
                continue
            evidence = self._resolve_refs(e.ev, index, project_id)
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
            evidence = self._resolve_refs(f.ev, index, project_id)
            findings.append(Finding(
                type=(f.type or "").upper().strip(),
                severity=(f.severity or "MEDIUM").upper().strip(),
                title=f.title.strip(),
                description=(f.description or "").strip(),
                evidence=evidence,
            ))

        # ── Sophistication ───────────────────────────────────────────────
        raw_score = parsed.sophistication.sophistication_score
        # Clamp defensively even though Pydantic already validates ge=0, le=100
        clamped_score = max(0, min(100, raw_score))
        sophistication_record = ProjectSophisticationRecord(
            project_name=project_id,
            sophistication_score=clamped_score,
            sophistication_tier=score_to_tier(clamped_score),
            sophistication_reasoning=(parsed.sophistication.sophistication_reasoning or "").strip(),
        )

        return {
            "technologies": technologies,
            "competencies": competencies,
            "ownership_signals": ownership_signals,
            "engineering_signals": engineering_signals,
            "findings": findings,
            "project_sophistication": [sophistication_record],
        }
