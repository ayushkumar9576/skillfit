"""
scripts/test_analysis_models.py
-------------------------------
Comprehensive verification and integrity test suite for SkillFit Phase 3.5:
Analysis Domain Models.

Covers:
    1. Pure Dataclass Instantiation across all 10 domain entities and base primitives
    2. Deep Nested Serialization via dataclasses.asdict()
    3. Partial Population of ResumeAnalysis (progressive lifecycle)
    4. Full Population of ResumeAnalysis (complete candidate profile)
    5. Evidence Linkage & Traceability (AnalysisEvidence attributes)
    6. Circular Import Prevention and Clean Top-Level Package Exports
    7. Type Integrity and Default Initializers
    8. Framework Coupling Isolation (0 SQLAlchemy, 0 FastAPI, 0 Pydantic, 0 OpenAI in app.analysis)
    9. Architecture Documentation Verification
"""

import ast
import os
import sys
import unittest
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone

sys.path.insert(0, ".")

# 1. Verify Top-Level Package Exports
from app.analysis import (
    AchievementAnalysisResult,
    AchievementEvidence,
    AnalysisEvidence,
    AnalysisMetadata,
    CandidateContact,
    CategoryScore,
    CertificationAnalysisResult,
    CertificationEvidence,
    EducationAnalysisResult,
    EducationEvidence,
    ExperienceAnalysisResult,
    ExperienceEvidence,
    InternshipAnalysisResult,
    InternshipEvidence,
    PositionOfResponsibilityAnalysisResult,
    PositionOfResponsibilityEvidence,
    ProjectAnalysisResult,
    ProjectEvidence,
    PublicationAnalysisResult,
    PublicationEvidence,
    ReadinessAnalysisResult,
    ResumeAnalysis,
    SkillAnalysisResult,
    SkillEvidence,
)


class TestBasePrimitives(unittest.TestCase):
    """Verify base domain primitives (AnalysisEvidence, AnalysisMetadata)."""

    def test_analysis_evidence_instantiation_and_defaults(self):
        evidence = AnalysisEvidence(
            evidence_text="Built microservice using FastAPI and PostgreSQL",
            source_section="projects",
            confidence=0.95,
            context_snippet="Under Projects section: Built microservice using FastAPI...",
            line_number=24,
        )
        self.assertTrue(is_dataclass(evidence))
        self.assertEqual(evidence.evidence_text, "Built microservice using FastAPI and PostgreSQL")
        self.assertEqual(evidence.source_section, "projects")
        self.assertEqual(evidence.confidence, 0.95)
        self.assertEqual(evidence.line_number, 24)

    def test_analysis_metadata_instantiation_and_datetime(self):
        now = datetime.now(timezone.utc)
        meta = AnalysisMetadata(
            source_resume_id="res-12345-uuid",
            analysis_version="3.5.0",
            generated_at=now,
            model_name="rule_based",
            execution_time_ms=12.5,
        )
        self.assertTrue(is_dataclass(meta))
        self.assertEqual(meta.source_resume_id, "res-12345-uuid")
        self.assertEqual(meta.analysis_version, "3.5.0")
        self.assertEqual(meta.generated_at, now)
        self.assertEqual(meta.model_name, "rule_based")
        self.assertEqual(meta.execution_time_ms, 12.5)

    def test_metadata_default_timestamp_is_datetime(self):
        meta = AnalysisMetadata(source_resume_id="res-abc")
        self.assertIsInstance(meta.generated_at, datetime)
        self.assertEqual(meta.analysis_version, "3.5.0")


class TestDomainModelInstantiation(unittest.TestCase):
    """Verify each individual domain model instantiates with proper attributes and types."""

    def test_skill_models(self):
        ev = AnalysisEvidence(evidence_text="FastAPI backend", source_section="skills")
        skill = SkillEvidence(
            skill_name="FastAPI",
            category="Backend Frameworks",
            proficiency_level="advanced",
            confidence=0.98,
            evidences=[ev],
        )
        res = SkillAnalysisResult(
            skills=[skill],
            total_skills_count=1,
            categories_breakdown={"Backend Frameworks": 1},
        )
        self.assertTrue(is_dataclass(skill))
        self.assertTrue(is_dataclass(res))
        self.assertEqual(len(res.skills), 1)
        self.assertEqual(res.skills[0].skill_name, "FastAPI")

    def test_project_models(self):
        ev = AnalysisEvidence(evidence_text="Designed task scheduler", source_section="projects")
        proj = ProjectEvidence(
            title="Distributed Queue",
            description="High-throughput distributed task scheduler in Go.",
            role="Backend Engineer",
            technologies=["Go", "Redis", "Docker"],
            project_url="https://github.com/example/queue",
            highlights=["Processed 10k tasks/sec", "Zero data loss"],
            confidence=0.96,
            evidences=[ev],
        )
        res = ProjectAnalysisResult(projects=[proj], total_projects_count=1)
        self.assertTrue(is_dataclass(proj))
        self.assertEqual(res.projects[0].technologies, ["Go", "Redis", "Docker"])

    def test_internship_models(self):
        ev = AnalysisEvidence(evidence_text="Summer intern at TechCorp", source_section="internships")
        intern = InternshipEvidence(
            organization="TechCorp India",
            role="Software Engineer Intern",
            duration="May 2025 - July 2025",
            location="Bangalore (Hybrid)",
            description="Built telemetry monitoring dashboard.",
            technologies_used=["Python", "React", "Grafana"],
            achievements=["Reduced alerting latency by 40%"],
            confidence=0.94,
            evidences=[ev],
        )
        res = InternshipAnalysisResult(internships=[intern], total_internships_count=1)
        self.assertEqual(res.internships[0].organization, "TechCorp India")

    def test_experience_models(self):
        ev = AnalysisEvidence(evidence_text="Full-time software engineer", source_section="experience")
        exp = ExperienceEvidence(
            organization="FinTech Labs",
            role="Associate Developer",
            duration="Aug 2024 - Present",
            location="Mumbai",
            description="Engineered payments gateway reconciliation service.",
            is_current=True,
            achievements=["Handled 5M daily transactions"],
            technologies_used=["Java", "Spring Boot", "Kafka"],
            confidence=0.99,
            evidences=[ev],
        )
        res = ExperienceAnalysisResult(experiences=[exp], total_experience_count=1)
        self.assertTrue(res.experiences[0].is_current)

    def test_education_models(self):
        ev = AnalysisEvidence(evidence_text="B.Tech Computer Science", source_section="education")
        edu = EducationEvidence(
            institution="National Institute of Technology",
            degree="B.Tech",
            field_of_study="Computer Science & Engineering",
            duration="2022 - 2026",
            grade_type="CGPA",
            grade_value="8.85 / 10.0",
            coursework=["Data Structures", "Operating Systems", "DBMS"],
            confidence=1.0,
            evidences=[ev],
        )
        res = EducationAnalysisResult(education_entries=[edu], highest_degree="B.Tech")
        self.assertEqual(res.education_entries[0].grade_value, "8.85 / 10.0")

    def test_certification_models(self):
        ev = AnalysisEvidence(evidence_text="AWS Certified Developer", source_section="certifications")
        cert = CertificationEvidence(
            certification_name="AWS Certified Developer Associate",
            issuer="Amazon Web Services",
            issue_date="2025",
            credential_id="AWS-DEV-98765",
            credential_url="https://aws.amazon.com/verify/98765",
            confidence=0.97,
            evidences=[ev],
        )
        res = CertificationAnalysisResult(certifications=[cert], total_certifications_count=1)
        self.assertEqual(res.certifications[0].issuer, "Amazon Web Services")

    def test_achievement_models(self):
        ev = AnalysisEvidence(evidence_text="1st place Smart India Hackathon", source_section="achievements")
        ach = AchievementEvidence(
            title="1st Place - Smart India Hackathon 2025",
            issuer="Ministry of Education, Govt of India",
            year="2025",
            description="Winner among 500+ teams in AI & Placement track.",
            confidence=0.95,
            evidences=[ev],
        )
        res = AchievementAnalysisResult(achievements=[ach], total_achievements_count=1)
        self.assertEqual(res.achievements[0].year, "2025")

    def test_leadership_models(self):
        ev = AnalysisEvidence(evidence_text="President, Coding Club", source_section="positions_of_responsibility")
        lead = PositionOfResponsibilityEvidence(
            title="President",
            organization="ACM Student Chapter",
            duration="2024 - 2025",
            description="Organized national hackathon and 12 technical workshops.",
            confidence=0.93,
            evidences=[ev],
        )
        res = PositionOfResponsibilityAnalysisResult(positions=[lead], total_positions_count=1)
        self.assertEqual(res.positions[0].organization, "ACM Student Chapter")

    def test_publication_models(self):
        ev = AnalysisEvidence(evidence_text="Published paper on NLP classification", source_section="publications")
        pub = PublicationEvidence(
            title="Adaptive Attention Mechanisms for Resume Parsing",
            publisher="IEEE Conference on AI",
            publication_date="2025",
            url="https://doi.org/10.1109/example",
            description="Introduced hybrid attention routing for unstructured documents.",
            authors=["Aarav Sharma", "Dr. S. K. Gupta"],
            confidence=0.96,
            evidences=[ev],
        )
        res = PublicationAnalysisResult(publications=[pub], total_publications_count=1)
        self.assertEqual(len(res.publications[0].authors), 2)

    def test_readiness_models(self):
        ev = AnalysisEvidence(evidence_text="Overall strong technical portfolio", source_section="summary")
        cat_skills = CategoryScore(category_name="Skills", score=90.0, max_score=100.0, weight=0.3)
        cat_projects = CategoryScore(category_name="Projects", score=85.0, max_score=100.0, weight=0.3)
        readiness = ReadinessAnalysisResult(
            overall_score=88.5,
            readiness_level="industry_ready",
            summary="Candidate demonstrates excellent backend architecture and practical project experience.",
            category_scores={"Skills": cat_skills, "Projects": cat_projects},
            strengths=["Strong core CS fundamentals", "Production-grade project deployment"],
            weaknesses=["Could gain more cloud infrastructure experience"],
            recommendations=["Earn AWS Solutions Architect certification"],
            key_risks=[],
            evidences=[ev],
        )
        self.assertEqual(readiness.readiness_level, "industry_ready")
        self.assertEqual(readiness.category_scores["Skills"].score, 90.0)


class TestAggregateResumeAnalysis(unittest.TestCase):
    """Verify partial, full, and nested lifecycle of ResumeAnalysis aggregate root."""

    def setUp(self):
        self.meta = AnalysisMetadata(
            source_resume_id="resume-uuid-001",
            analysis_version="3.5.0",
            model_name="rule_based",
        )

    def test_partial_population(self):
        """Verify ResumeAnalysis can be partially instantiated during progressive pipeline execution."""
        analysis = ResumeAnalysis(metadata=self.meta)
        self.assertEqual(analysis.metadata.source_resume_id, "resume-uuid-001")
        self.assertIsNone(analysis.skills)
        self.assertIsNone(analysis.projects)
        self.assertIsNone(analysis.internships)
        self.assertIsNone(analysis.experience)
        self.assertIsNone(analysis.education)
        self.assertIsNone(analysis.certifications)
        self.assertIsNone(analysis.achievements)
        self.assertIsNone(analysis.positions_of_responsibility)
        self.assertIsNone(analysis.publications)
        self.assertIsNone(analysis.readiness)
        self.assertEqual(analysis.extensions, {})

    def test_full_progressive_population_and_serialization(self):
        """Verify complete population across all 10 domain facets and serialization to nested dict."""
        contact = CandidateContact(
            full_name="Aarav Sharma",
            email="aarav@example.com",
            phone="+91 9876543210",
            github_url="https://github.com/aarav",
            linkedin_url="https://linkedin.com/in/aarav",
        )

        skill_ev = AnalysisEvidence(evidence_text="Python programming", source_section="skills")
        skills = SkillAnalysisResult(
            skills=[SkillEvidence(skill_name="Python", category="Languages", confidence=0.98, evidences=[skill_ev])],
            total_skills_count=1,
        )

        proj_ev = AnalysisEvidence(evidence_text="SkillFit placement portal", source_section="projects")
        projects = ProjectAnalysisResult(
            projects=[ProjectEvidence(title="SkillFit", description="Platform", technologies=["FastAPI"], evidences=[proj_ev])],
            total_projects_count=1,
        )

        edu_ev = AnalysisEvidence(evidence_text="B.Tech NIT", source_section="education")
        education = EducationAnalysisResult(
            education_entries=[EducationEvidence(institution="NIT", degree="B.Tech", evidences=[edu_ev])],
            highest_degree="B.Tech",
        )

        readiness = ReadinessAnalysisResult(
            overall_score=85.0,
            readiness_level="advanced",
            summary="Strong candidate",
            strengths=["FastAPI", "Python"],
        )

        analysis = ResumeAnalysis(
            metadata=self.meta,
            contact=contact,
            skills=skills,
            projects=projects,
            education=education,
            readiness=readiness,
            extensions={"ats_score": 92.5},
        )

        # 1. Verify object structure
        self.assertEqual(analysis.contact.full_name, "Aarav Sharma")
        self.assertEqual(analysis.skills.skills[0].skill_name, "Python")
        self.assertEqual(analysis.projects.projects[0].title, "SkillFit")
        self.assertEqual(analysis.readiness.overall_score, 85.0)
        self.assertEqual(analysis.extensions["ats_score"], 92.5)

        # 2. Verify deep nested serialization
        serialized = asdict(analysis)
        self.assertIsInstance(serialized, dict)
        self.assertEqual(serialized["metadata"]["source_resume_id"], "resume-uuid-001")
        self.assertEqual(serialized["contact"]["full_name"], "Aarav Sharma")
        self.assertEqual(serialized["skills"]["skills"][0]["skill_name"], "Python")
        self.assertEqual(serialized["skills"]["skills"][0]["evidences"][0]["evidence_text"], "Python programming")
        self.assertEqual(serialized["extensions"]["ats_score"], 92.5)


class TestFrameworkIsolation(unittest.TestCase):
    """
    Verify architectural purity: guarantee that app/analysis contains ZERO
    imports of SQLAlchemy, FastAPI, Pydantic, or OpenAI SDK.
    """

    FORBIDDEN_MODULES = {"sqlalchemy", "fastapi", "pydantic", "openai", "langchain"}

    def test_no_forbidden_framework_imports(self):
        models_dir = os.path.join("app", "analysis", "models")
        for filename in os.listdir(models_dir):
            if filename.endswith(".py"):
                filepath = os.path.join(models_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=filepath)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            root_pkg = alias.name.split(".")[0].lower()
                            self.assertNotIn(
                                root_pkg,
                                self.FORBIDDEN_MODULES,
                                f"Forbidden framework import '{alias.name}' detected in {filepath}",
                            )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            root_pkg = node.module.split(".")[0].lower()
                            self.assertNotIn(
                                root_pkg,
                                self.FORBIDDEN_MODULES,
                                f"Forbidden framework import 'from {node.module}' detected in {filepath}",
                            )


class TestDocumentationIntegrity(unittest.TestCase):
    """Verify that the Phase 3.5 architecture documentation exists and is comprehensive."""

    def test_architecture_doc_exists_and_populated(self):
        doc_path = os.path.join("..", "docs", "architecture", "phase_3_5_analysis_models.md")
        self.assertTrue(os.path.isfile(doc_path), f"Architecture documentation missing at {doc_path}")
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertGreater(len(content), 1000, "Architecture documentation is unexpectedly short.")
        self.assertIn("ResumeAnalysis", content)
        self.assertIn("AnalysisEvidence", content)
        self.assertIn("AnalysisMetadata", content)


def run_tests():
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n" + "=" * 60)
        print("ALL PHASE 3.5 ANALYSIS DOMAIN MODEL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "!" * 60)
        print(f"FAILED: {len(result.failures)} failures, {len(result.errors)} errors")
        print("!" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
