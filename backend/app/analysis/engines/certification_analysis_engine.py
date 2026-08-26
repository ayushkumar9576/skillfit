"""
app/analysis/engines/certification_analysis_engine.py
-----------------------------------------------------
The SkillFit Certification Analysis Engine (Phase 3.9).

Orchestrates the highly token-optimized, batched intelligence pipeline for certifications.
Features:
    - Batch processing (up to 5 per prompt).
    - Partial batch recovery (salvages valid certs if a batch fails).
    - Hallucination defense (evidence rehydration).
    - Cost verification metrics logging.
    - Deterministic recognition logic (provider tiers + keywords).
"""

import asyncio
import logging
import os
import json
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from app.analysis.models.base import AnalysisEvidence
from app.analysis.models.certification_models import (
    CertificationAnalysisResult,
    CertificationEvidence,
    CertificationIntelligenceReport,
    ExecutiveAssessment,
    ScoredDimension,
    SkillSignal,
    PROVIDER_UNKNOWN,
)
from app.analysis.engines.certification_schemas import (
    CertificationBatchIntelligence,
    CertificationIntelligence,
)
from app.services.llm.exceptions import LLMError, LLMResponseError
from app.services.llm.service import LLMService, get_llm_service

logger = logging.getLogger(__name__)

DEFAULT_ANALYSIS_MAX_TOKENS: int = 4000
ANALYZER_NAME: str = "certification"
_EVIDENCE_SECTION: str = "certifications"
BATCH_SIZE = 5

_RECOGNITION_KEYWORDS = frozenset({
    "professional", "associate", "expert", "architect", 
    "engineer", "specialist", "practitioner"
})


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


class CertificationAnalysisEngine:
    """
    Evidence-based certification analysis orchestrator.
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

    def analyze(
        self, *, resume_id: str, certifications: List[CertificationEvidence]
    ) -> CertificationAnalysisResult:
        """Synchronous wrapper for analyze_async."""
        return asyncio.run(self.analyze_async(resume_id=resume_id, certifications=certifications))

    async def analyze_async(
        self, *, resume_id: str, certifications: List[CertificationEvidence]
    ) -> CertificationAnalysisResult:
        result = CertificationAnalysisResult(
            certifications=certifications,
            total_certifications_count=len(certifications)
        )
        if not result.certifications:
            logger.info("Certification analysis: no certifications provided for resume %s; skipping LLM.", resume_id)
            return result

        llm = self._get_llm_service()
        logger.info("Starting analysis for %d certification(s) [Resume %s]", len(certifications), resume_id)

        # Batch the certifications
        batches = [certifications[i:i + BATCH_SIZE] for i in range(0, len(certifications), BATCH_SIZE)]
        reports: List[CertificationIntelligenceReport] = []

        # Process batches concurrently
        tasks = [
            self._analyze_batch_with_recovery(llm, resume_id, batch, batch_idx, len(batches))
            for batch_idx, batch in enumerate(batches)
        ]
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for br in batch_results:
            if isinstance(br, Exception):
                logger.error("Unhandled exception in certification batch task: %s", str(br), exc_info=br)
            elif br:
                reports.extend(br)

        result.reports = reports
        logger.info("Successfully analyzed %d/%d certifications [Resume %s]", len(reports), len(certifications), resume_id)
        return result

    # -- internal batching & recovery ----------------------------------------

    async def _analyze_batch_with_recovery(
        self, llm: LLMService, resume_id: str, batch: List[CertificationEvidence], batch_idx: int, total_batches: int
    ) -> List[CertificationIntelligenceReport]:
        """
        Analyzes a batch of certifications. If the batch fails validation, attempts partial recovery
        by analyzing them individually (or falling back safely).
        """
        try:
            return await self._analyze_batch(llm, resume_id, batch, batch_idx, total_batches)
        except (LLMResponseError, ValidationError) as e:
            logger.warning(
                "Batch %d/%d failed validation (%s). Attempting partial batch recovery for %d certifications.", 
                batch_idx + 1, total_batches, str(e), len(batch)
            )
            # Partial Recovery: Analyze individually
            recovered_reports = []
            for idx, single_cert in enumerate(batch):
                try:
                    single_batch = [single_cert]
                    res = await self._analyze_batch(llm, resume_id, single_batch, batch_idx, total_batches, is_recovery=True)
                    recovered_reports.extend(res)
                except Exception as inner_e:
                    logger.warning("Recovery failed for certification '%s' (Index %d in batch %d). Discarding. Error: %s", 
                                   single_cert.certification_name, idx, batch_idx + 1, str(inner_e))
            return recovered_reports
        except Exception as e:
            logger.error("Unexpected error in batch %d/%d: %s", batch_idx + 1, total_batches, str(e))
            return []

    async def _analyze_batch(
        self, llm: LLMService, resume_id: str, batch: List[CertificationEvidence], batch_idx: int, total_batches: int, is_recovery: bool = False
    ) -> List[CertificationIntelligenceReport]:
        
        # Build prompt payload
        evidence_payload = self._build_batch_payload(batch)
        
        context = {
            "batch_size": len(batch),
            "schema_name": "CertificationBatchIntelligence"
        }

        # LLM Call
        response = await llm.analyze(
            analyzer=ANALYZER_NAME,
            data=evidence_payload,
            prompt_vars=context,
            response_schema=CertificationBatchIntelligence,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        # Cost Verification Metrics Logging
        mode_str = "RECOVERY" if is_recovery else "BATCH"
        logger.info(
            "Cost Metrics [%s %d/%d]: certs_processed=%d",
            mode_str, batch_idx + 1, total_batches, len(batch)
        )

        batch_output: CertificationBatchIntelligence = response
        reports = []

        # Map to intelligence reports
        # The LLM is supposed to return a list of certifications in the exact order requested.
        for idx, cert_intel in enumerate(batch_output.certifications):
            if idx >= len(batch):
                logger.warning("LLM returned more certifications than requested. Truncating.")
                break
                
            source_cert = batch[idx]
            report = self._map_to_report(cert_intel, source_cert)
            reports.append(report)

        return reports

    # -- payload generation --------------------------------------------------

    def _build_batch_payload(self, batch: List[CertificationEvidence]) -> str:
        """
        Builds a highly compact JSON payload for the batch of certifications.
        """
        payloads = []
        for idx, cert in enumerate(batch):
            ev_list = []
            for line_ev in cert.evidences:
                ev_list.append({"line": line_ev.line_number, "text": line_ev.evidence_text})
                
            payloads.append({
                "certification_index": idx,
                "title": cert.certification_name,
                "provider": cert.issuer,
                "evidence": ev_list
            })
            
        return json.dumps(payloads, ensure_ascii=False)

    # -- mapping & hydration -------------------------------------------------

    def _map_to_report(self, intel: CertificationIntelligence, source: CertificationEvidence) -> CertificationIntelligenceReport:
        # 1. Deterministic signals
        provider_tier = source.issuer if source.issuer else PROVIDER_UNKNOWN
        
        title_lower = source.certification_name.lower()
        has_recognition_keyword = any(kw in title_lower for kw in _RECOGNITION_KEYWORDS)
        
        # Build lookup dict for hydration
        ev_lookup = {e.line_number: e for e in source.evidences}

        # 2. Map dimensions
        def _hydrate(refs: List[int]) -> List[AnalysisEvidence]:
            hydrated = []
            for ref in refs:
                if ref in ev_lookup:
                    hydrated.append(ev_lookup[ref])
                else:
                    logger.warning("Hallucinated or out-of-range evidence ref: %d in certification '%s'", ref, source.certification_name)
            return hydrated

        def _map_scored_dim(schema_dim, name: str) -> ScoredDimension:
            return ScoredDimension(
                name=name,
                score=schema_dim.score,
                confidence=schema_dim.confidence,
                reasoning=schema_dim.reasoning,
                classification=schema_dim.classification,
                evidence=_hydrate(schema_dim.ev)
            )

        cert_rec = _map_scored_dim(intel.certification_recognition, "certification_recognition")
        # Boost/adjust deterministically if applicable
        if has_recognition_keyword and cert_rec.score < 50:
            cert_rec.score = min(cert_rec.score + 10, 100)
            
        skill_signals = []
        for s in intel.skill_signals:
            skill_signals.append(SkillSignal(
                name=s.name,
                confidence=s.confidence,
                reasoning=s.reasoning,
                evidence=_hydrate(s.ev)
            ))
            
        exec_assess = ExecutiveAssessment(
            overall_value=intel.executive_assessment.overall_value,
            strongest_signal=intel.executive_assessment.strongest_signal,
            primary_limitation=intel.executive_assessment.primary_limitation
        )

        return CertificationIntelligenceReport(
            certification_name=source.certification_name,
            source_certification=source,
            provider_tier=provider_tier,
            certification_recognition=cert_rec,
            skill_signals=skill_signals,
            industry_relevance=_map_scored_dim(intel.industry_relevance, "industry_relevance"),
            hiring_signal=_map_scored_dim(intel.hiring_signal, "hiring_signal"),
            evidence_strength=_map_scored_dim(intel.evidence_strength, "evidence_strength"),
            executive_assessment=exec_assess,
            overall_confidence=intel.overall_confidence,
            caveats=intel.caveats
        )

    def _get_llm_service(self) -> LLMService:
        if self._llm_service:
            return self._llm_service
        return get_llm_service()
