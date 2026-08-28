"""
app/analysis/engines/readiness_engine.py
----------------------------------------
Readiness Engine for SkillFit Phase 3.11.

Aggregates structured evidence from Projects, Internships, Certifications,
and Skills to compute a deterministic Placement Readiness score.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from app.analysis.models.project_models import ProjectAnalysisResult
from app.analysis.models.internship_models import InternshipAnalysisResult
from app.analysis.models.certification_models import (
    CertificationAnalysisResult,
    PROVIDER_HIGH,
    PROVIDER_MEDIUM,
    PROVIDER_LOW,
    PROVIDER_UNKNOWN,
)
from app.analysis.models.skill_models import SkillAnalysisResult
from app.analysis.models.readiness_models import (
    ReadinessAnalysisResult,
    ReadinessLevel,
    AnalysisStatus,
    Severity,
    ScoreBreakdown,
    ReadinessStrength,
    ReadinessGap,
    HIRING_SIGNAL_WEIGHTS,
    DEPTH_ADVANCED,
    DEPTH_INTERMEDIATE,
    DEPTH_BEGINNER,
)

logger = logging.getLogger(__name__)


def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    return max(min_val, min(value, max_val))


def _severity_to_int(severity: Severity) -> int:
    if severity == Severity.HIGH:
        return 3
    if severity == Severity.MEDIUM:
        return 2
    return 1


class ReadinessEngine:
    def __init__(self):
        self.weights = {
            "projects": 0.45,
            "internships": 0.15,
            "certifications": 0.10,
            "skills": 0.30,
        }

    def analyze(
        self,
        resume_id: str,
        project_result: Optional[ProjectAnalysisResult],
        internship_result: Optional[InternshipAnalysisResult],
        certification_result: Optional[CertificationAnalysisResult],
        skill_result: Optional[SkillAnalysisResult],
    ) -> ReadinessAnalysisResult:
        try:
            return self._analyze_internal(
                resume_id,
                project_result,
                internship_result,
                certification_result,
                skill_result,
            )
        except Exception as exc:
            logger.exception("Readiness Engine critical failure.")
            return self._empty_result(
                resume_id, status=AnalysisStatus.FAILED
            )

    def _analyze_internal(
        self,
        resume_id: str,
        project_result: Optional[ProjectAnalysisResult],
        internship_result: Optional[InternshipAnalysisResult],
        certification_result: Optional[CertificationAnalysisResult],
        skill_result: Optional[SkillAnalysisResult],
    ) -> ReadinessAnalysisResult:
        
        status = AnalysisStatus.SUCCESS

        # Handle None inputs safely
        project_count = project_result.total_projects_count if project_result else 0
        internship_count = internship_result.total_internships_count if internship_result else 0
        certification_count = certification_result.total_certifications_count if certification_result else 0
        skill_count = skill_result.total_skills_count if skill_result else 0

        p_reports = project_result.reports if project_result and project_result.reports else []
        i_reports = internship_result.reports if internship_result and internship_result.reports else []
        c_reports = certification_result.reports if certification_result and certification_result.reports else []
        s_profiles = skill_result.skills if skill_result and skill_result.skills else []



        # 1. Project Score
        project_score = 0.0
        avg_project_conf = 0.0
        project_contributors = {
            "complexity": 0.0,
            "engineering_depth": 0.0,
            "technical_maturity": 0.0,
            "industry_relevance": 0.0
        }
        if p_reports:
            total_conf = 0.0
            
            # Map maturity to score
            maturity_scores = {
                "prototype": 20.0,
                "academic": 40.0,
                "portfolio": 60.0,
                "production_like": 80.0,
                "industry_level": 100.0,
            }
            
            project_raw_scores = []
            
            for report in p_reports:
                conf = _clamp(report.overall_confidence if getattr(report, "overall_confidence", 0.0) > 0 else 1.0)
                
                c_score = getattr(report.complexity.overall, "score", 0.0)
                d_score = getattr(report.engineering_depth, "score", 0.0)
                i_score = getattr(report.industry_relevance, "score", 0.0)
                
                maturity_class = getattr(report.technical_maturity, "classification", "")
                m_score = maturity_scores.get(maturity_class.lower(), 20.0)
                
                # Internal Project Weights
                proj_score = (c_score * 0.30) + (d_score * 0.30) + (m_score * 0.25) + (i_score * 0.15)
                
                # Apply extraction confidence
                proj_score = proj_score * conf
                
                project_raw_scores.append({
                    "score": proj_score,
                    "c_score": c_score,
                    "d_score": d_score,
                    "i_score": i_score,
                    "m_score": m_score,
                    "conf": conf
                })
                total_conf += conf
                
            # Sort projects by score descending
            project_raw_scores.sort(key=lambda x: x["score"], reverse=True)
            
            # Apply decayed summation to prevent quantity from beating quality
            # First project = 1.0x, Second = 0.3x, Third = 0.1x, Rest = 0.0x
            decay_weights = [1.0, 0.3, 0.1]
            total_proj_score = 0.0
            
            for idx, p_info in enumerate(project_raw_scores):
                if idx < len(decay_weights):
                    weight = decay_weights[idx]
                    total_proj_score += p_info["score"] * weight
                    
                    # Accumulate for explainability (normalized to 100 max)
                    project_contributors["complexity"] += p_info["c_score"] * 0.30 * weight
                    project_contributors["engineering_depth"] += p_info["d_score"] * 0.30 * weight
                    project_contributors["technical_maturity"] += p_info["m_score"] * 0.25 * weight
                    project_contributors["industry_relevance"] += p_info["i_score"] * 0.15 * weight

            project_score = _clamp(total_proj_score, 0.0, 100.0)
            avg_project_conf = _clamp(total_conf / len(p_reports))
        elif project_count > 0:
            # Extraction succeeded, but intelligence failed
            status = AnalysisStatus.PARTIAL

        # 2. Internship Score
        internship_score = 0.0
        avg_intern_conf = 0.0
        if i_reports:
            total_intern_score = 0.0
            total_conf = 0.0
            for report in i_reports:
                conf = _clamp(report.hiring_signal.confidence)
                sig_score = report.hiring_signal.score
                if sig_score >= 80.0:
                    signal_str = "HIGH"
                elif sig_score >= 50.0:
                    signal_str = "MEDIUM"
                else:
                    signal_str = "LOW"
                signal_weight = HIRING_SIGNAL_WEIGHTS.get(signal_str, 40.0)
                
                total_intern_score += 25.0 * (signal_weight / 100.0) * conf
                total_conf += conf
            
            internship_score = _clamp(total_intern_score, 0.0, 100.0)
            avg_intern_conf = _clamp(total_conf / len(i_reports))
        elif internship_count > 0:
            status = AnalysisStatus.PARTIAL

        # 3. Certification Score
        certification_score = 0.0
        avg_cert_conf = 0.0
        if c_reports:
            total_cert_score = 0.0
            total_conf = 0.0
            for report in c_reports:
                conf = _clamp(report.hiring_signal.confidence if hasattr(report, "hiring_signal") else 1.0)
                
                tier = report.provider_tier
                if tier == PROVIDER_HIGH:
                    tier_mult = 1.0
                elif tier == PROVIDER_MEDIUM:
                    tier_mult = 0.75
                elif tier == PROVIDER_LOW:
                    tier_mult = 0.5
                else:
                    tier_mult = 0.25
                
                total_cert_score += 20.0 * tier_mult * conf
                total_conf += conf
            
            certification_score = _clamp(total_cert_score, 0.0, 100.0)
            avg_cert_conf = _clamp(total_conf / len(c_reports))
        elif certification_count > 0:
            status = AnalysisStatus.PARTIAL

        # 4. Skill Score
        skill_score = 0.0
        avg_skill_conf = 0.0
        adv_skills = 0
        int_skills = 0
        beg_skills = 0
        high_signal_skills = 0
        med_signal_skills = 0
        low_signal_skills = 0
        
        if s_profiles:
            total_skill_points = 0.0
            total_conf = 0.0
            
            for profile in s_profiles:
                conf = _clamp(profile.confidence_score)
                depth = (profile.skill_depth or "BEGINNER").upper()
                signal_str = (profile.hiring_signal or "LOW").upper()
                
                if depth == DEPTH_ADVANCED:
                    depth_val = 15.0
                    adv_skills += 1
                elif depth == DEPTH_INTERMEDIATE:
                    depth_val = 8.0
                    int_skills += 1
                else:
                    depth_val = 3.0
                    beg_skills += 1
                    
                if signal_str == "HIGH":
                    high_signal_skills += 1
                    is_high_signal = True
                elif signal_str == "MEDIUM":
                    med_signal_skills += 1
                    is_high_signal = False
                else:
                    low_signal_skills += 1
                    is_high_signal = False
                
                points = depth_val * conf * (1.0 if is_high_signal else 0.5)
                total_skill_points += points
                total_conf += conf
                
            skill_score = _clamp(total_skill_points, 0.0, 100.0)
            avg_skill_conf = _clamp(total_conf / len(s_profiles))
        elif skill_count > 0:
            status = AnalysisStatus.PARTIAL

        # Final Readiness Calculation
        readiness_score = _clamp(
            (project_score * self.weights["projects"]) +
            (internship_score * self.weights["internships"]) +
            (certification_score * self.weights["certifications"]) +
            (skill_score * self.weights["skills"]),
            0.0, 100.0
        )
        
        if readiness_score >= 80.0:
            readiness_level = ReadinessLevel.HIGH
        elif readiness_score >= 60.0:
            readiness_level = ReadinessLevel.MEDIUM
        else:
            readiness_level = ReadinessLevel.LOW

        # Confidence Renormalization
        active_weight_sum = 0.0
        weighted_conf_sum = 0.0

        if project_count > 0:
            active_weight_sum += self.weights["projects"]
            weighted_conf_sum += (avg_project_conf * self.weights["projects"])
        if internship_count > 0:
            active_weight_sum += self.weights["internships"]
            weighted_conf_sum += (avg_intern_conf * self.weights["internships"])
        if certification_count > 0:
            active_weight_sum += self.weights["certifications"]
            weighted_conf_sum += (avg_cert_conf * self.weights["certifications"])
        if skill_count > 0:
            active_weight_sum += self.weights["skills"]
            weighted_conf_sum += (avg_skill_conf * self.weights["skills"])

        if active_weight_sum > 0:
            overall_confidence = _clamp(weighted_conf_sum / active_weight_sum)
        else:
            overall_confidence = 0.0

        # Evidence Deduplication
        seen = set()
        
        def _add_evidence(evidences):
            for ev in evidences:
                key = (ev.source_section, ev.evidence_text, ev.line_number)
                seen.add(key)
                
        if p_reports:
            for report in p_reports:
                if report.source_project:
                    _add_evidence(report.source_project.evidences)
        if i_reports:
            for report in i_reports:
                if report.source_internship:
                    _add_evidence(report.source_internship.evidences)
        if c_reports:
            for report in c_reports:
                if report.source_certification:
                    _add_evidence(report.source_certification.evidences)
        if s_profiles:
            for profile in s_profiles:
                for source in profile.evidences:
                    _add_evidence(source.evidences)

        evidence_count = len(seen)

        # Strengths & Gaps
        strengths: List[ReadinessStrength] = []
        gaps: List[ReadinessGap] = []

        # Hard Gap Rules & Diagnostics
        if project_count == 0:
            gaps.append(ReadinessGap(title="No Projects", severity=Severity.HIGH, reasoning="No project experience detected."))
        elif len(p_reports) == 0:
            gaps.append(ReadinessGap(title="Project Analysis Incomplete", severity=Severity.HIGH, reasoning="Projects were extracted but analysis failed."))
        elif project_score >= 80.0:
            strengths.append(ReadinessStrength(title="Strong Project Portfolio", evidence_count=len(p_reports), reasoning=f"Demonstrated {len(p_reports)} high-quality projects.", impact_score=project_score * self.weights["projects"]))

        if internship_count == 0:
            gaps.append(ReadinessGap(title="No Internships", severity=Severity.MEDIUM, reasoning="No industry internship experience detected."))
        elif len(i_reports) == 0:
            gaps.append(ReadinessGap(title="Internship Analysis Incomplete", severity=Severity.MEDIUM, reasoning="Internships were extracted but analysis failed."))
        elif internship_score >= 80.0:
            strengths.append(ReadinessStrength(title="Strong Internship Exposure", evidence_count=len(i_reports), reasoning=f"Demonstrated {len(i_reports)} strong industry internships.", impact_score=internship_score * self.weights["internships"]))

        if certification_count == 0:
            gaps.append(ReadinessGap(title="No Certifications", severity=Severity.LOW, reasoning="No external certifications detected."))
        elif len(c_reports) == 0:
            gaps.append(ReadinessGap(title="Certification Analysis Incomplete", severity=Severity.LOW, reasoning="Certifications were extracted but analysis failed."))
        elif certification_score >= 80.0:
            strengths.append(ReadinessStrength(title="Strong Certification Profile", evidence_count=len(c_reports), reasoning=f"Demonstrated {len(c_reports)} highly recognized certifications.", impact_score=certification_score * self.weights["certifications"]))

        if high_signal_skills == 0 and skill_count > 0:
            gaps.append(ReadinessGap(title="No High-Confidence Skills", severity=Severity.HIGH, reasoning="No skills passed the high-signal threshold."))
        
        if adv_skills >= 3:
            strengths.append(ReadinessStrength(title="Extensive Advanced Skill Base", evidence_count=adv_skills, reasoning=f"Demonstrated {adv_skills} advanced technical skills.", impact_score=skill_score * self.weights["skills"]))

        # Sort and truncate
        strengths.sort(key=lambda s: (-s.impact_score, s.title, -s.evidence_count))
        gaps.sort(key=lambda g: (-_severity_to_int(g.severity), g.title))
        
        strengths = strengths[:5]
        gaps = gaps[:5]

        return ReadinessAnalysisResult(
            resume_id=resume_id,
            engine_version="3.11.0",
            analysis_status=status,
            readiness_score=readiness_score,
            readiness_level=readiness_level,
            overall_confidence=overall_confidence,
            score_breakdown=ScoreBreakdown(
                project_score=project_score,
                internship_score=internship_score,
                certification_score=certification_score,
                skill_score=skill_score,
                project_contributors=project_contributors,
            ),
            strengths=strengths,
            gaps=gaps,
            advanced_skill_count=adv_skills,
            intermediate_skill_count=int_skills,
            beginner_skill_count=beg_skills,
            high_signal_skill_count=high_signal_skills,
            medium_signal_skill_count=med_signal_skills,
            low_signal_skill_count=low_signal_skills,
            project_count=project_count,
            internship_count=internship_count,
            certification_count=certification_count,
            skill_count=skill_count,
            evidence_count=evidence_count,
            generated_at=datetime.now(timezone.utc),
        )

    def _empty_result(self, resume_id: str, status: AnalysisStatus) -> ReadinessAnalysisResult:
        return ReadinessAnalysisResult(
            resume_id=resume_id,
            engine_version="3.11.0",
            analysis_status=status,
            readiness_score=0.0,
            readiness_level=ReadinessLevel.LOW,
            overall_confidence=0.0,
            score_breakdown=ScoreBreakdown(
                project_score=0.0,
                internship_score=0.0,
                certification_score=0.0,
                skill_score=0.0,
            ),
            strengths=[],
            gaps=[],
            advanced_skill_count=0,
            intermediate_skill_count=0,
            beginner_skill_count=0,
            high_signal_skill_count=0,
            medium_signal_skill_count=0,
            low_signal_skill_count=0,
            project_count=0,
            internship_count=0,
            certification_count=0,
            skill_count=0,
            evidence_count=0,
            generated_at=datetime.now(timezone.utc),
        )
