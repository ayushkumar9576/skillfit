"""
app/analysis/engines/project_analysis_engine.py
------------------------------------------------
The SkillFit Project Analysis Engine (Phase 3.7).

Orchestrates the evidence-based, per-project intelligence pipeline:

    raw resume text
        │  (rule-based)
        ▼
    RuleBasedProjectExtractor  ->  [ProjectEvidence, ...]
        │  (one LLM analysis call per project, in parallel)
        ▼
    LLMService.analyze(analyzer="project", response_schema=ProjectIntelligence)
        │  (validated Pydantic -> pure dataclass, evidence rehydrated by line)
        ▼
    [ProjectIntelligenceReport, ...]   attached to ProjectAnalysisResult.reports

Key contracts (all reinforced by the phase spec):
    - **Provider-agnostic model.** The engine passes ``model=self._model`` which
      defaults to ``None`` — the runtime-configured ``LLM_MODEL`` is used. No
      model name is ever hardcoded here.
    - **Compact wire, full report.** The model returns the deliberately small
      ``ProjectIntelligence`` wire schema; this module reconstructs the complete
      :class:`ProjectIntelligenceReport` from it. Three reconstructions do the
      heavy lifting (see "Reconstruction" below): evidence rehydration, the
      confidence band, and the skills/tech fan-out. Because the response is much
      smaller, truncation is rare and the output-token bill per project is a
      fraction of what a fully-inlined schema costs.
    - **Resilience.** Per-project failures are logged and skipped, so one bad
      project never sinks the rest. A missing/invalid key surfaces as
      ``LLMConfigurationError`` from service construction and propagates to the
      caller (the pipeline stage downgrades it to a graceful skip).
    - **No persistence.** Phase 3.7 returns the in-memory dataclass artifact
      only; persistence is Phase 3.12.

Reconstruction
==============
1. **Evidence by line reference.** The model cites ``"ev": [4, 7]`` instead of
   re-quoting resume text. :meth:`_resolve_refs` rehydrates each reference from a
   per-project line index built off ``ProjectEvidence.evidences``, which already
   carries ``line_number``, ``context_snippet``, and an extraction confidence.
   The mapped :class:`AnalysisEvidence` therefore ends up *richer* than the old
   inlined form (which left ``line_number`` and ``context_snippet`` empty), and a
   reference that resolves to nothing is detectable — a fabricated quote was not.
2. **Confidence band.** ``confidence_level`` is derived from the numeric
   ``confidence`` by :func:`_confidence_band`, so the model transmits one number
   instead of a number *and* a redundant label.
3. **Skills/tech fan-out.** One ``skills_and_tech`` entry becomes both a
   ``TechnologyUsage`` row and a ``SkillEvidenceItem``, and the four
   claimed/demonstrated/verified/unverified lists are grouped from the items'
   statuses rather than transmitted.

Async boundary:
    :meth:`analyze_async` is the real implementation. :meth:`analyze` is a thin
    ``asyncio.run`` wrapper for sync callers (the background pipeline stage runs
    in a worker thread with no running loop, so ``asyncio.run`` is safe there —
    exactly as sanctioned by ``app/services/llm/service.py``).
"""

import asyncio
import logging
import os
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple

from app.analysis.models.base import AnalysisEvidence
from app.analysis.models.project_models import (
    ArchitectureFacet,
    AssessedPoint,
    Competency,
    ComplexityAssessment,
    ExecutiveAssessment,
    MissingEvidenceItem,
    ProjectAnalysisResult,
    ProjectEvidence,
    ProjectIntelligenceReport,
    ProjectUnderstanding,
    SKILL_CLAIMED,
    SKILL_DEMONSTRATED,
    SKILL_UNVERIFIED,
    SKILL_VERIFIED,
    ScoredDimension,
    SkillEvidenceItem,
    SkillEvidenceMap,
    TechnicalMaturity,
    TechnologyUsage,
)
from app.analysis.engines.project_schemas import (
    ArchitectureFacetSchema,
    AssessedPointSchema,
    CompetencySchema,
    EvidenceRef,
    ExecutiveAssessmentSchema,
    ProjectIntelligence,
    ScoredDimensionSchema,
    SkillTechSchema,
    TechnicalMaturitySchema,
    UnderstandingSchema,
)
from app.services.llm.exceptions import LLMError
from app.services.llm.service import LLMService, get_llm_service
from app.services.resume.project_extractor import (
    BaseProjectExtractor,
    get_project_extractor,
)

logger = logging.getLogger(__name__)

#: Default output-token budget for one project report. The compact wire schema
#: brings a full 16-area report in well under this, so the cap is headroom rather
#: than a constraint — which is what keeps truncation rare.
DEFAULT_ANALYSIS_MAX_TOKENS: int = 8000

#: Analyzer name -> selects prompt "project_analysis" and labels usage records.
ANALYZER_NAME: str = "project"

#: Section stamped on evidence mapped back out of the LLM response.
_EVIDENCE_SECTION: str = "projects"

#: Every score in the report is on a 0–100 scale, so ``max_score`` is a constant
#: the mapper supplies rather than a value the model wastes output tokens echoing.
_MAX_SCORE: float = 100.0

#: Confidence thresholds for :func:`_confidence_band`. Ordered high -> low.
_BAND_VERIFIED: float = 0.75
_BAND_LIKELY: float = 0.40

#: Canonical skill statuses -> the report list each one populates.
_STATUS_TO_LIST: Dict[str, str] = {
    SKILL_CLAIMED: "claimed",
    SKILL_DEMONSTRATED: "demonstrated",
    SKILL_VERIFIED: "verified",
    SKILL_UNVERIFIED: "unverified",
}

#: ``kind`` hints that force an entry to be treated as a technology / a skill.
_KIND_TECH = frozenset({"tech", "technology", "technologies"})
_KIND_SKILL = frozenset({"skill", "skills", "competency"})

#: Leading list punctuation the extractor keeps in ``context_snippet`` but strips
#: from ``evidence_text``. Deliberately excludes letters/digits/'.'/')' so a real
#: word is never mangled by ``str.lstrip``.
_BULLET_CHARS: str = " \t-–—*+•·‣▪>"


def _context_adds_signal(text: str, context: str) -> bool:
    """
    Decide whether an evidence's context snippet is worth sending to the model.

    The extractor defaults ``context_snippet`` to the evidence text itself, and
    for a bullet it is the same sentence with the list marker still attached — so
    sending it unconditionally nearly doubled the input payload to convey "this
    was a bullet", which ``highlight_lines`` already says. Context is therefore
    emitted only when it differs by more than list punctuation.

    Nothing is lost in the report either way: :meth:`_resolve_refs` rehydrates
    ``context_snippet`` from the extractor's own record, not from the payload.
    """
    if not context:
        return False
    return context.lstrip(_BULLET_CHARS).strip() != text.lstrip(_BULLET_CHARS).strip()


def _resolve_max_tokens(explicit: Optional[int]) -> int:
    """
    Resolve the per-call output budget.

    Precedence: explicit arg > ``LLM_MAX_TOKENS`` env var > 8000.
    """
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


def _confidence_band(confidence: float) -> str:
    """
    Derive the coarse ``confidence_level`` label from the numeric confidence.

    The model transmits only the number; the label is a pure function of it, so
    asking for both would be two encodings of one fact. A confidence of exactly
    0.0 is the "we could not substantiate this at all" case — which is precisely
    what an omitted dimension defaults to — and maps to ``cannot_verify``.

    Returns:
        One of ``"verified"``, ``"likely"``, ``"uncertain"``, ``"cannot_verify"``.
    """
    if confidence <= 0.0:
        return "cannot_verify"
    if confidence >= _BAND_VERIFIED:
        return "verified"
    if confidence >= _BAND_LIKELY:
        return "likely"
    return "uncertain"


def _normalize_name(name: str) -> str:
    """Fold a technology/skill name for case- and punctuation-tolerant matching."""
    return "".join(ch for ch in name.lower() if ch.isalnum())


class ProjectAnalysisEngine:
    """
    Evidence-based project analysis orchestrator.

    Every collaborator is injectable so the engine is fully unit-testable with a
    fake provider and no network/key.

    Args:
        llm_service: Injected :class:`LLMService`. When ``None``, the process
            singleton is obtained lazily on first use (which validates config
            and may raise ``LLMConfigurationError`` if no key is present).
        extractor: Injected project extractor. Defaults to the rule-based one.
        model: Provider model override. **Defaults to ``None``** so the
            runtime-configured ``LLM_MODEL`` is used — never hardcode a model.
        max_tokens: Per-call output cap override. When ``None``, resolved from
            ``LLM_MAX_TOKENS`` env, else :data:`DEFAULT_ANALYSIS_MAX_TOKENS`.
        temperature: Sampling temperature (default 0.0 for determinism).
    """

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

    # -- public API ---------------------------------------------------------

    async def analyze_async(
        self, *, resume_id: str, raw_text: str
    ) -> ProjectAnalysisResult:
        """
        Extract projects from ``raw_text`` and analyze each one.

        Returns a :class:`ProjectAnalysisResult` with ``projects`` (extraction)
        and ``reports`` (per-project intelligence). When no projects are found,
        returns early WITHOUT constructing/using the LLM service (0 provider
        calls) — which also keeps keyless environments quiet.
        """
        result = self._extractor.extract(raw_text)
        if not result.projects:
            logger.info(
                "Project analysis: no projects extracted for resume %s; skipping LLM.",
                resume_id,
            )
            return result

        llm = self._get_llm_service()
        logger.info(
            "Project analysis: analyzing %d project(s) for resume %s (max_tokens=%d).",
            len(result.projects), resume_id, self._max_tokens,
        )

        # Snapshot the usage log so the batch's own token cost can be reported
        # below. Safe because project analysis is the only analyzer driving this
        # service during the gather.
        usage_offset = len(llm.usage_tracker.records)

        reports = await asyncio.gather(
            *(self._analyze_one(index, project, llm)
              for index, project in enumerate(result.projects))
        )
        result.reports = [report for report in reports if report is not None]

        self._log_output_cost(llm, usage_offset, resume_id)
        logger.info(
            "Project analysis complete for resume %s: %d/%d report(s) generated.",
            resume_id, len(result.reports), len(result.projects),
        )
        return result

    def analyze(self, *, resume_id: str, raw_text: str) -> ProjectAnalysisResult:
        """
        Synchronous wrapper around :meth:`analyze_async`.

        Safe to call from a sync context with no running event loop (e.g. the
        background pipeline stage's worker thread). Do NOT call from inside a
        running loop — use :meth:`analyze_async` there instead.
        """
        return asyncio.run(self.analyze_async(resume_id=resume_id, raw_text=raw_text))

    # -- internals ----------------------------------------------------------

    def _get_llm_service(self) -> LLMService:
        if self._llm_service is None:
            self._llm_service = get_llm_service()
        return self._llm_service

    @staticmethod
    def _log_output_cost(llm: LLMService, offset: int, resume_id: str) -> None:
        """
        Report this batch's completion-token cost at INFO.

        Output size is the whole point of the compact wire schema, so it is worth
        observing rather than assuming. Never raises — a logging convenience must
        not be able to fail an analysis.
        """
        try:
            batch = llm.usage_tracker.records[offset:]
            if not batch:
                return
            completion = sum(record.completion_tokens for record in batch)
            prompt = sum(record.prompt_tokens for record in batch)
            logger.info(
                "Project analysis token cost for resume %s: %d call(s), "
                "%d prompt + %d completion tokens (mean %d completion/project).",
                resume_id, len(batch), prompt, completion, completion // len(batch),
            )
        except Exception:  # noqa: BLE001 - observability must never break analysis
            logger.debug("Project analysis: could not summarize token usage.", exc_info=True)

    async def _analyze_one(
        self, index: int, project: ProjectEvidence, llm: LLMService
    ) -> Optional[ProjectIntelligenceReport]:
        """Analyze a single project; log + skip (return ``None``) on failure."""
        payload = self._build_payload(project)
        try:
            parsed = await llm.analyze(
                analyzer=ANALYZER_NAME,
                data=payload,
                response_schema=ProjectIntelligence,
                model=self._model,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            return self._map_report(project, parsed)
        except LLMError as exc:
            logger.warning(
                "Project analysis: skipping project #%d (%s) — %s: %s",
                index, project.title, type(exc).__name__, exc,
            )
            return None
        except Exception as exc:  # noqa: BLE001 - best-effort, never sink siblings
            logger.error(
                "Project analysis: unexpected error on project #%d (%s) — %s: %s",
                index, project.title, type(exc).__name__, exc,
            )
            return None

    # -- payload construction ----------------------------------------------

    @staticmethod
    def _build_payload(project: ProjectEvidence) -> Dict[str, Any]:
        """
        Build the JSON evidence payload sent to the LLM.

        ``evidence`` is the line-numbered spine of the payload and the only thing
        the model may cite. It is a complete superset of the extractor's
        ``highlights`` and ``description`` — every project line becomes an
        evidence entry (see ``RuleBasedProjectExtractor._parse_segment``) — so
        those two fields are NOT re-sent as text. Bullets are instead flagged by
        line via ``highlight_lines``, preserving the structural signal at a
        fraction of the input-token cost.

        ``context`` is emitted only when it genuinely adds signal beyond the text
        (see :func:`_context_adds_signal`). The extractor defaults
        ``context_snippet`` to the text itself — and to the same sentence with the
        bullet marker still attached for a highlight — so sending it
        unconditionally duplicated most of the payload for nothing.
        """
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
        # Only send the optional parsed fields when the extractor actually found
        # them — a run of `"role": null, "project_url": null` is pure overhead.
        if project.role:
            payload["role"] = project.role
        if project.project_url:
            payload["project_url"] = project.project_url
        if highlight_lines:
            payload["highlight_lines"] = highlight_lines
        return payload

    # -- evidence rehydration ----------------------------------------------

    @staticmethod
    def _build_line_index(project: ProjectEvidence) -> Dict[int, AnalysisEvidence]:
        """
        Index the project's extracted evidence by resume line number.

        This is what makes citation-by-reference possible: the model returns line
        numbers and the engine restores the full evidence record. The first entry
        for a line wins (the extractor emits at most one per line).
        """
        index: Dict[int, AnalysisEvidence] = {}
        for ev in project.evidences:
            if ev.line_number is not None and ev.line_number not in index:
                index[ev.line_number] = ev
        return index

    def _resolve_refs(
        self,
        refs: Sequence[EvidenceRef],
        index: Dict[int, AnalysisEvidence],
        fallback_confidence: float,
    ) -> List[AnalysisEvidence]:
        """
        Turn the model's ``ev`` citations into full :class:`AnalysisEvidence`.

        An ``int`` is a line reference resolved against ``index``; the rehydrated
        record carries the extractor's own text, context snippet, line number, and
        extraction confidence — all of it verbatim from the resume, so it cannot
        be a paraphrase. A reference that matches no line is dropped with a debug
        log (the model cited something that does not exist).

        A ``str`` is the tolerated fallback for a model that quoted text instead
        of citing a line. It is preserved as evidence text with no line number,
        taking ``fallback_confidence`` (the confidence of the finding it supports)
        since no extraction confidence is available for it.

        Duplicate references within one finding are collapsed.
        """
        resolved: List[AnalysisEvidence] = []
        seen: Set[EvidenceRef] = set()

        for ref in refs:
            if isinstance(ref, int):
                source = index.get(ref)
                if source is None:
                    logger.debug(
                        "Project analysis: dropping unresolvable evidence line ref %r.", ref
                    )
                    continue
                if ref in seen:
                    continue
                seen.add(ref)
                # A fresh instance per finding: the same line legitimately backs
                # many findings, and sharing one mutable dataclass across them
                # would couple otherwise-independent parts of the report.
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
        self, project: ProjectEvidence, parsed: ProjectIntelligence
    ) -> ProjectIntelligenceReport:
        """Map a validated :class:`ProjectIntelligence` onto the dataclass report."""
        index = self._build_line_index(project)

        complexity = ComplexityAssessment(
            overall=self._scored(parsed.complexity.overall, "overall", index),
            backend=self._scored(parsed.complexity.backend, "backend", index),
            frontend=self._scored(parsed.complexity.frontend, "frontend", index),
            database=self._scored(parsed.complexity.database, "database", index),
            system_design=self._scored(parsed.complexity.system_design, "system_design", index),
            integration=self._scored(parsed.complexity.integration, "integration", index),
            deployment=self._scored(parsed.complexity.deployment, "deployment", index),
        )

        technology_usage, skill_evidence = self._fan_out_skills_and_tech(
            parsed.skills_and_tech, project.technologies, index
        )

        return ProjectIntelligenceReport(
            project_title=project.title,
            source_project=project,
            understanding=self._understanding(parsed.understanding, index),
            architecture=[self._facet(a, index) for a in parsed.architecture],
            complexity=complexity,
            engineering_depth=self._scored(
                parsed.engineering_depth, "engineering_depth", index
            ),
            technology_usage=technology_usage,
            competencies=[self._competency(c, index) for c in parsed.competencies],
            skill_evidence=skill_evidence,
            industry_relevance=self._scored(
                parsed.industry_relevance, "industry_relevance", index
            ),
            technical_maturity=self._maturity(parsed.technical_maturity, index),
            evidence_strength=self._scored(
                parsed.evidence_strength, "evidence_strength", index
            ),
            hiring_signal=self._scored(parsed.hiring_signal, "hiring_signal", index),
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
        """
        Decide whether a ``skills_and_tech`` entry is also a ``technology_usage`` row.

        An explicit ``kind`` hint from the model wins. Without one, the project's
        own extracted technology list is the oracle — it comes straight from the
        resume's "Technologies:" line, so it is a reliable answer to "is this a
        named technology". When that list is empty (a project with no tech line),
        fall back to treating anything the model gave a depth score as a
        technology, so ``technology_usage`` is never spuriously empty.
        """
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
        """
        Expand the merged ``skills_and_tech`` wire array into both report views.

        Returns ``(technology_usage, skill_evidence)``:
            - every entry becomes a :class:`SkillEvidenceItem`, so nothing is lost;
            - technology-like entries additionally become a :class:`TechnologyUsage`;
            - the four claimed/demonstrated/verified/unverified lists are grouped
              from the items' statuses instead of being transmitted separately.

        An unrecognized ``status`` still lands in ``items`` verbatim (the report
        stores classifications as-is) but is not forced into one of the four
        lists, so a cosmetic mismatch never silently mislabels a skill.
        """
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
                        # Independent instances per view — see _resolve_refs.
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
        self, u: UnderstandingSchema, index: Dict[int, AnalysisEvidence]
    ) -> ProjectUnderstanding:
        return ProjectUnderstanding(
            purpose=u.purpose or "",
            problem_solved=u.problem_solved or "",
            intended_users=u.intended_users or "",
            domain=u.domain or "",
            project_type=u.project_type or "",
            business_value=u.business_value or "",
            confidence=u.confidence,
            confidence_level=_confidence_band(u.confidence),
            evidence=self._resolve_refs(u.ev, index, u.confidence),
        )

    def _facet(
        self, a: ArchitectureFacetSchema, index: Dict[int, AnalysisEvidence]
    ) -> ArchitectureFacet:
        return ArchitectureFacet(
            area=a.area or "",
            assessment=a.assessment or "",
            score=a.score,
            max_score=_MAX_SCORE,
            confidence=a.confidence,
            confidence_level=_confidence_band(a.confidence),
            evidence=self._resolve_refs(a.ev, index, a.confidence),
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

    def _maturity(
        self, tm: TechnicalMaturitySchema, index: Dict[int, AnalysisEvidence]
    ) -> TechnicalMaturity:
        return TechnicalMaturity(
            classification=tm.classification or "",
            score=tm.score,
            max_score=_MAX_SCORE,
            confidence=tm.confidence,
            confidence_level=_confidence_band(tm.confidence),
            reasoning=tm.reasoning or "",
            evidence=self._resolve_refs(tm.ev, index, tm.confidence),
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
