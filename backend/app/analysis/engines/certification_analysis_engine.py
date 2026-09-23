"""
app/analysis/engines/certification_analysis_engine.py
-----------------------------------------------------
SkillFit Certification Analysis Engine — Phase 3 Remediation.

Orchestrates the batched certification intelligence pipeline.
Calls the LLM with the new CertificationBatchIntelligence schema
and maps results to CertificationIntelligence objects from candidate_profile.py.

LLM infrastructure (batching, partial recovery, token control) is unchanged.
Only the mapper layer (_map_to_report) has been replaced.
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from app.analysis.models.candidate_profile import (
    CertificationIntelligence,
    IntelligenceEvidence,
    IntelligenceSourceType,
)
from app.analysis.engines.certification_schemas import (
    CertificationBatchIntelligence,
    CertificationIntelligenceSchema,
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


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class CertificationAnalysisResult:
    """Container for certification intelligence objects."""
    certifications: List[Any] = field(default_factory=list)
    total_certifications_count: int = 0
    intelligence: List[CertificationIntelligence] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CertificationAnalysisEngine:
    """
    Evidence-based certification analysis orchestrator — Phase 3 Remediation.

    Batched LLM call → CertificationBatchIntelligence schema →
    CertificationIntelligence objects from candidate_profile.py.
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

    def analyze(
        self, *, resume_id: str, certifications: List[Any]
    ) -> CertificationAnalysisResult:
        return asyncio.run(
            self.analyze_async(resume_id=resume_id, certifications=certifications)
        )

    async def analyze_async(
        self, *, resume_id: str, certifications: List[Any]
    ) -> CertificationAnalysisResult:
        result = CertificationAnalysisResult(
            certifications=certifications,
            total_certifications_count=len(certifications),
        )
        if not certifications:
            logger.info(
                "Certification analysis: no certifications for resume %s; skipping.", resume_id
            )
            return result

        llm = self._get_llm_service()
        
        print("\033[96m\n" + "="*50)
        print(f"🚀 DETECTED {len(certifications)} CERTIFICATIONS FOR ANALYSIS")
        for i, cert in enumerate(certifications, 1):
            print(f"   {i}. {getattr(cert, 'certification_name', 'Unknown Certification')}")
        print("="*50 + "\n\033[0m")

        batches = [
            certifications[i:i + BATCH_SIZE]
            for i in range(0, len(certifications), BATCH_SIZE)
        ]
        tasks = [
            self._analyze_batch_with_recovery(llm, resume_id, batch, idx, len(batches))
            for idx, batch in enumerate(batches)
        ]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for br in batch_results:
            if isinstance(br, Exception):
                logger.error("Unhandled exception in certification batch: %s", str(br), exc_info=br)
            elif br:
                result.intelligence.extend(br)

        logger.info(
            "Certification analysis complete for resume %s: %d/%d processed.",
            resume_id, len(result.intelligence), len(certifications),
        )
        return result

    # -- batch / recovery ----------------------------------------------------

    async def _analyze_batch_with_recovery(
        self,
        llm: LLMService,
        resume_id: str,
        batch: List[Any],
        batch_idx: int,
        total_batches: int,
    ) -> List[CertificationIntelligence]:
        try:
            return await self._analyze_batch(llm, resume_id, batch, batch_idx, total_batches)
        except (LLMResponseError, ValidationError) as e:
            logger.warning(
                "Batch %d/%d failed validation (%s). Attempting partial recovery for %d certs.",
                batch_idx + 1, total_batches, str(e), len(batch),
            )
            recovered: List[CertificationIntelligence] = []
            for idx, single_cert in enumerate(batch):
                try:
                    res = await self._analyze_batch(
                        llm, resume_id, [single_cert], batch_idx, total_batches,
                        is_recovery=True,
                    )
                    recovered.extend(res)
                except Exception as inner_e:
                    logger.warning(
                        "Recovery failed for certification '%s' (idx %d in batch %d): %s",
                        getattr(single_cert, "certification_name", "unknown"),
                        idx, batch_idx + 1, str(inner_e),
                    )
            return recovered
        except Exception as e:
            logger.error("Unexpected error in batch %d/%d: %s", batch_idx + 1, total_batches, str(e))
            return []

    async def _analyze_batch(
        self,
        llm: LLMService,
        resume_id: str,
        batch: List[Any],
        batch_idx: int,
        total_batches: int,
        is_recovery: bool = False,
    ) -> List[CertificationIntelligence]:
        evidence_payload = self._build_batch_payload(batch)
        context = {
            "batch_size": len(batch),
            "schema_name": "CertificationBatchIntelligence",
        }

        response: CertificationBatchIntelligence = await llm.analyze(
            analyzer=ANALYZER_NAME,
            data=evidence_payload,
            prompt_vars=context,
            response_schema=CertificationBatchIntelligence,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        mode_str = "RECOVERY" if is_recovery else "BATCH"
        logger.info(
            "Cost Metrics [%s %d/%d]: certs_processed=%d",
            mode_str, batch_idx + 1, total_batches, len(batch),
        )

        results: List[CertificationIntelligence] = []
        for idx, cert_intel in enumerate(response.certifications):
            if idx >= len(batch):
                logger.warning("LLM returned more certifications than requested. Truncating.")
                break
            source_cert = batch[idx]
            results.append(self._map_to_report(cert_intel, source_cert))
        return results

    # -- payload generation --------------------------------------------------

    @staticmethod
    def _build_batch_payload(batch: List[Any]) -> str:
        payloads = []
        for idx, cert in enumerate(batch):
            ev_list = []
            for line_ev in (getattr(cert, "evidences", []) or []):
                ev_list.append({
                    "line": line_ev.line_number,
                    "text": line_ev.evidence_text,
                })
            payloads.append({
                "certification_index": idx,
                "title": getattr(cert, "certification_name", ""),
                "provider": getattr(cert, "issuer", ""),
                "evidence": ev_list,
            })
        return json.dumps(payloads, ensure_ascii=False)

    # -- Mapper: CertificationIntelligenceSchema → CertificationIntelligence --

    def _map_to_report(
        self,
        intel: CertificationIntelligenceSchema,
        source: Any,
    ) -> CertificationIntelligence:
        cert_name = getattr(source, "certification_name", "") or ""
        issuer = getattr(source, "issuer", "") or ""

        # Build evidence from source evidences
        evidence: List[IntelligenceEvidence] = []
        ev_lookup = {
            e.line_number: e
            for e in (getattr(source, "evidences", []) or [])
            if e.line_number is not None
        }
        for ev_obj in (getattr(source, "evidences", []) or []):
            evidence.append(IntelligenceEvidence(
                source=IntelligenceSourceType.CERTIFICATION,
                source_id=cert_name,
                section=_EVIDENCE_SECTION,
                quote=(ev_obj.evidence_text or "").strip(),
                line_reference=ev_obj.line_number,
            ))

        # Deterministic recognition boost
        title_lower = cert_name.lower()
        has_recognition_keyword = any(kw in title_lower for kw in _RECOGNITION_KEYWORDS)
        industry_recognition = intel.industry_recognition or "unknown"
        if has_recognition_keyword and industry_recognition in ("low", "unknown"):
            industry_recognition = "moderate"

        return CertificationIntelligence(
            certification_name=cert_name,
            category=intel.category or "",
            supported_competencies=[c.upper() for c in (intel.supported_competencies or []) if c],
            supported_domains=[d.upper() for d in (intel.supported_domains or []) if d],
            industry_recognition=industry_recognition,
            practical_strength=intel.practical_strength or "theory-heavy",
            limitations=list(intel.limitations or []),
            evidence=evidence,
        )

    def _get_llm_service(self) -> LLMService:
        if self._llm_service:
            return self._llm_service
        return get_llm_service()
