import pytest
from unittest.mock import AsyncMock, patch

from app.analysis.models.base import AnalysisEvidence
from app.analysis.models.internship_models import (
    InternshipEvidence,
    InternshipAnalysisResult,
    InternshipIntelligenceReport
)
from app.analysis.engines.internship_schemas import (
    InternshipIntelligence,
    InternshipUnderstandingSchema,
    ScoredDimensionSchema,
    OwnershipClassificationSchema,
    SkillTechSchema,
    WorkplaceMaturitySchema,
    ExecutiveAssessmentSchema
)
from app.analysis.engines.internship_analysis_engine import InternshipAnalysisEngine
from app.services.llm.exceptions import LLMError


@pytest.fixture
def mock_llm_service():
    service = AsyncMock()
    return service


@pytest.fixture
def engine(mock_llm_service):
    return InternshipAnalysisEngine(llm_service=mock_llm_service)


@pytest.fixture
def sample_internship():
    return InternshipEvidence(
        organization="Test Corp",
        role="SWE Intern",
        description="Built cool things.",
        technologies_used=["Python", "AWS"],
        achievements=["Improved latency by 20%."],
        evidences=[
            AnalysisEvidence(evidence_text="Built cool things.", source_section="internships", line_number=1, confidence=0.9),
            AnalysisEvidence(evidence_text="Improved latency by 20%.", source_section="internships", line_number=2, confidence=0.9)
        ]
    )


@pytest.mark.asyncio
async def test_analyze_async_happy_path(engine, mock_llm_service, sample_internship):
    mock_intelligence = InternshipIntelligence(
        understanding=InternshipUnderstandingSchema(purpose="Testing", confidence=0.9, ev=[1]),
        technical_depth=ScoredDimensionSchema(score=80.0, confidence=0.9, ev=[1]),
        engineering_ownership=OwnershipClassificationSchema(classification="owner", score=85.0, confidence=0.9, ev=[1]),
        collaboration_exposure=ScoredDimensionSchema(score=70.0, confidence=0.9, ev=[1]),
        impact_analysis=ScoredDimensionSchema(score=90.0, confidence=0.9, ev=[2]),
        production_exposure=ScoredDimensionSchema(score=75.0, confidence=0.8, ev=[1]),
        software_engineering_practices=ScoredDimensionSchema(score=80.0, confidence=0.8, ev=[1]),
        skills_and_tech=[
            SkillTechSchema(name="Python", kind="tech", depth=85.0, status="verified", confidence=0.9, ev=[1])
        ],
        competencies=[],
        industry_readiness=ScoredDimensionSchema(score=85.0, confidence=0.9, ev=[2]),
        hiring_signal=ScoredDimensionSchema(score=90.0, confidence=0.9, ev=[2]),
        internship_quality="strong",
        workplace_maturity=WorkplaceMaturitySchema(classification="production_like", score=80.0, confidence=0.9, ev=[1]),
        executive_assessment=ExecutiveAssessmentSchema(overall_impression="Great intern", overall_confidence=0.9),
        overall_confidence=0.9
    )
    
    mock_llm_service.analyze.return_value = mock_intelligence

    result = await engine.analyze_async(resume_id="res-123", internships=[sample_internship])

    assert isinstance(result, InternshipAnalysisResult)
    assert len(result.reports) == 1
    report = result.reports[0]
    
    assert report.internship_role == "SWE Intern"
    assert report.internship_organization == "Test Corp"
    assert report.understanding.purpose == "Testing"
    assert report.technical_depth.score == 80.0
    assert report.engineering_ownership.classification == "owner"
    assert report.technology_usage[0].technology == "Python"
    assert report.internship_quality == "strong"
    assert report.overall_confidence_level == "verified"
    
    mock_llm_service.analyze.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_async_empty_internships(engine, mock_llm_service):
    result = await engine.analyze_async(resume_id="res-123", internships=[])
    assert result.total_internships_count == 0
    assert len(result.reports) == 0
    mock_llm_service.analyze.assert_not_called()


@pytest.mark.asyncio
async def test_analyze_async_llm_error_skips_project(engine, mock_llm_service, sample_internship):
    mock_llm_service.analyze.side_effect = LLMError("API Timeout")
    
    result = await engine.analyze_async(resume_id="res-123", internships=[sample_internship])
    
    assert result.total_internships_count == 1
    assert len(result.reports) == 0


@pytest.mark.asyncio
async def test_evidence_rehydration(engine, mock_llm_service, sample_internship):
    mock_intelligence = InternshipIntelligence()
    mock_intelligence.understanding = InternshipUnderstandingSchema(purpose="Testing", confidence=0.9, ev=[1, 2])
    
    mock_llm_service.analyze.return_value = mock_intelligence
    result = await engine.analyze_async(resume_id="res-123", internships=[sample_internship])
    
    report = result.reports[0]
    ev = report.understanding.evidence
    
    assert len(ev) == 2
    assert ev[0].line_number == 1
    assert ev[0].evidence_text == "Built cool things."
    assert ev[1].line_number == 2
    assert ev[1].evidence_text == "Improved latency by 20%."


@pytest.mark.asyncio
async def test_unresolvable_evidence_dropped(engine, mock_llm_service, sample_internship):
    mock_intelligence = InternshipIntelligence()
    # 99 is unresolvable
    mock_intelligence.understanding = InternshipUnderstandingSchema(purpose="Testing", confidence=0.9, ev=[1, 99])
    
    mock_llm_service.analyze.return_value = mock_intelligence
    result = await engine.analyze_async(resume_id="res-123", internships=[sample_internship])
    
    report = result.reports[0]
    ev = report.understanding.evidence
    
    assert len(ev) == 1
    assert ev[0].line_number == 1
