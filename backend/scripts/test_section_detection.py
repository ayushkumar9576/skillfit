"""
scripts/test_section_detection.py
---------------------------------
Comprehensive verification and regression test suite for SkillFit Phase 3.4:
Resume Section Detection.

Covers:
    1. Realistic End-to-End Resume Fixtures (Fresh Graduate, Internship Candidate, Experienced Student)
    2. Canonical 12-Section Schema Compliance (zero nulls, zero omitted keys)
    3. Robust Header Normalization (case, decorators, bullets, markdown, numbers, punctuation)
    4. Expanded Student Alias Mapping across all canonical categories
    5. Content Preservation (pre-header contact capture, unknown content in 'other', 0 text loss)
    6. Edge Cases (empty text, whitespace only, single section, randomized section order)
    7. False Positive Guardrails (narrative sentences containing keywords rejected as headers)
    8. Deterministic Core Coverage Confidence Metric (0.0 to 1.0)
    9. Extensible Strategy Hierarchy & Factory Verification (RuleBased, LLM stub, Hybrid stub)
    10. Service Layer Integration (detect_sections_from_text)
"""

import sys
import unittest

sys.path.insert(0, ".")

from app.services.resume.section_types import (
    CANONICAL_SECTIONS,
    DetectionMetrics,
    ResumeSection,
    SectionDetectionResult,
    create_empty_sections,
)
from app.services.resume.section_headers import (
    SECTION_HEADER_MAP,
    match_section_header,
    normalize_header_text,
)
from app.services.resume.section_detector import (
    BaseSectionDetector,
    HybridSectionDetector,
    LLMSectionDetector,
    RuleBasedSectionDetector,
    get_section_detector,
)
from app.services.resume.section_service import (
    detect_sections_from_text,
)


class TestResumeSectionTypes(unittest.TestCase):
    """Verify section types, enum values, and default data structures."""

    def test_canonical_sections_count_and_members(self):
        self.assertEqual(len(CANONICAL_SECTIONS), 12)
        expected = {
            "contact", "summary", "education", "skills", "projects", "internships",
            "experience", "certifications", "achievements",
            "positions_of_responsibility", "publications", "other"
        }
        self.assertEqual(set(CANONICAL_SECTIONS), expected)

    def test_create_empty_sections_contract(self):
        empty_dict = create_empty_sections()
        self.assertEqual(len(empty_dict), 12)
        for key in CANONICAL_SECTIONS:
            self.assertIn(key, empty_dict)
            self.assertEqual(empty_dict[key], "")
            self.assertIsNotNone(empty_dict[key])


class TestHeaderNormalization(unittest.TestCase):
    """Verify normalization of various header formats and decorators."""

    def test_basic_casing_and_whitespace(self):
        self.assertEqual(normalize_header_text("EDUCATION"), "education")
        self.assertEqual(normalize_header_text("   Education   "), "education")
        self.assertEqual(normalize_header_text("technical skills"), "technical skills")

    def test_markdown_and_decorators(self):
        self.assertEqual(normalize_header_text("### EDUCATION"), "education")
        self.assertEqual(normalize_header_text("**TECHNICAL SKILLS**"), "technical skills")
        self.assertEqual(normalize_header_text("=== PROJECTS ==="), "projects")
        self.assertEqual(normalize_header_text("--- WORK EXPERIENCE ---"), "work experience")
        self.assertEqual(normalize_header_text("*** CERTIFICATIONS ***"), "certifications")
        self.assertEqual(normalize_header_text("[EDUCATION]"), "education")

    def test_bullets_and_numbers(self):
        self.assertEqual(normalize_header_text("• SKILLS"), "skills")
        self.assertEqual(normalize_header_text("● EXPERIENCE"), "experience")
        self.assertEqual(normalize_header_text("▪ ACHIEVEMENTS"), "achievements")
        self.assertEqual(normalize_header_text("- PROJECTS"), "projects")
        self.assertEqual(normalize_header_text("1. Education:"), "education")
        self.assertEqual(normalize_header_text("2) Technical Skills -"), "technical skills")
        self.assertEqual(normalize_header_text("I. Projects"), "projects")

    def test_trailing_punctuation(self):
        self.assertEqual(normalize_header_text("Education:"), "education")
        self.assertEqual(normalize_header_text("Projects -"), "projects")
        self.assertEqual(normalize_header_text("Experience |"), "experience")
        self.assertEqual(normalize_header_text("Skills /"), "skills")


class TestHeaderMatchingAndAliases(unittest.TestCase):
    """Verify alias mapping across student resume categories and rejection of false positives."""

    def test_skills_aliases(self):
        aliases = [
            "Skills", "Technical Skills", "Tools & Technologies", "Tech Stack",
            "Programming Languages", "Technical Proficiencies", "Core Competencies",
            "Frameworks & Tools", "Relevant Skills"
        ]
        for alias in aliases:
            self.assertEqual(
                match_section_header(alias),
                ResumeSection.SKILLS,
                f"Failed to match skills alias: {alias}",
            )

    def test_projects_aliases(self):
        aliases = [
            "Projects", "Academic Projects", "Personal Projects", "Key Projects",
            "Major Projects", "Capstone Project", "Project Work", "Engineering Projects"
        ]
        for alias in aliases:
            self.assertEqual(
                match_section_header(alias),
                ResumeSection.PROJECTS,
                f"Failed to match projects alias: {alias}",
            )

    def test_experience_aliases(self):
        aliases = [
            "Experience", "Work Experience", "Professional Experience",
            "Employment History", "Career History", "Work History", "Professional Background"
        ]
        for alias in aliases:
            self.assertEqual(
                match_section_header(alias),
                ResumeSection.EXPERIENCE,
                f"Failed to match experience alias: {alias}",
            )

    def test_internships_aliases(self):
        aliases = [
            "Internships", "Internship Experience", "Industrial Training",
            "Summer Internship", "Practical Training", "Virtual Internship"
        ]
        for alias in aliases:
            self.assertEqual(
                match_section_header(alias),
                ResumeSection.INTERNSHIPS,
                f"Failed to match internships alias: {alias}",
            )

    def test_positions_of_responsibility_aliases(self):
        aliases = [
            "Positions of Responsibility", "Leadership Experience",
            "Extracurricular Leadership", "Leadership Roles", "Campus Leadership",
            "Extracurricular Activities", "Volunteering", "Volunteer Work",
            "Clubs & Committees", "Activities & Leadership"
        ]
        for alias in aliases:
            self.assertEqual(
                match_section_header(alias),
                ResumeSection.POSITIONS_OF_RESPONSIBILITY,
                f"Failed to match positions of responsibility alias: {alias}",
            )

    def test_achievements_aliases(self):
        aliases = [
            "Achievements", "Awards & Achievements", "Honors & Awards",
            "Accomplishments", "Key Achievements", "Recognition"
        ]
        for alias in aliases:
            self.assertEqual(
                match_section_header(alias),
                ResumeSection.ACHIEVEMENTS,
                f"Failed to match achievements alias: {alias}",
            )

    def test_false_positive_guardrails(self):
        sentences = [
            "I have strong skills in Python and Django.",
            "Worked as a lead developer on the project management application.",
            "Responsible for designing database schemas and optimizing SQL queries.",
            "Developed an automated resume parser using FastAPI and PyPDF.",
            "Experienced in building microservices with Docker and Kubernetes.",
            "This is a very long narrative line that definitely should not be classified as a header.",
        ]
        for sentence in sentences:
            self.assertIsNone(
                match_section_header(sentence),
                f"False positive detected on sentence: '{sentence}'",
            )


class TestRealResumeFixtures(unittest.TestCase):
    """Test full parsing flow with realistic end-to-end resume fixtures."""

    def setUp(self):
        self.detector = RuleBasedSectionDetector()

    def test_fresh_graduate_resume_fixture(self):
        resume_text = """
Aarav Sharma
aarav.sharma@example.com | +91 9876543210
github.com/aaravsharma | linkedin.com/in/aaravsharma

EDUCATION
B.Tech in Computer Science and Engineering
National Institute of Technology (2022 - 2026)
CGPA: 8.85 / 10.0

TECHNICAL SKILLS
Languages: Python, C++, SQL, JavaScript
Frameworks & Tools: FastAPI, React, Git, Docker, PostgreSQL

PROJECTS
SkillFit Placement Portal
- Architected automated resume extraction pipeline with FastAPI and SQLAlchemy
- Integrated JWT authentication and role-based access control (RBAC)

Smart Campus Navigation System
- Implemented Dijkstra's pathfinding algorithm for campus maps
- Built mobile-responsive frontend using React and TailwindCSS
"""
        result = self.detector.detect_sections(resume_text)

        # 1. Verify all 12 canonical keys present
        self.assertEqual(len(result.sections), 12)
        for key in CANONICAL_SECTIONS:
            self.assertIn(key, result.sections)
            self.assertIsInstance(result.sections[key], str)

        # 2. Verify contact section captured pre-header info
        self.assertIn("Aarav Sharma", result.sections["contact"])
        self.assertIn("aarav.sharma@example.com", result.sections["contact"])

        # 3. Verify education section
        self.assertIn("B.Tech in Computer Science", result.sections["education"])
        self.assertIn("CGPA: 8.85", result.sections["education"])

        # 4. Verify skills section
        self.assertIn("Python, C++, SQL", result.sections["skills"])

        # 5. Verify projects section
        self.assertIn("SkillFit Placement Portal", result.sections["projects"])
        self.assertIn("Smart Campus Navigation", result.sections["projects"])

        # 6. Verify empty sections remain empty strings (not None)
        self.assertEqual(result.sections["experience"], "")
        self.assertEqual(result.sections["internships"], "")
        self.assertEqual(result.sections["certifications"], "")
        self.assertEqual(result.sections["publications"], "")

        # 7. Verify deterministic metrics (3 core sections: education, skills, projects)
        self.assertTrue(result.metrics.has_contact_info)
        self.assertEqual(result.metrics.parsing_confidence, 0.75)
        self.assertIn("education", result.metrics.detected_sections)
        self.assertIn("skills", result.metrics.detected_sections)
        self.assertIn("projects", result.metrics.detected_sections)

    def test_internship_candidate_resume_fixture(self):
        resume_text = """
Priya Patel
priya.patel@email.com | +91 9123456789
linkedin.com/in/priyapatel

=== ACADEMIC BACKGROUND ===
B.E. Information Technology, Pune University
Expected Graduation: 2026 | GPA: 9.1/10.0

=== INTERNSHIP EXPERIENCE ===
Backend Engineering Intern | CloudTech Solutions (May 2025 - July 2025)
- Designed REST APIs with FastAPI and async PostgreSQL drivers
- Optimized database query response times by 35%

=== RELEVANT PROJECTS ===
Distributed Task Queue
- Built lightweight message queue in Go using Redis streams

=== TOOLS & TECHNOLOGIES ===
Python, Go, Docker, Redis, PostgreSQL, AWS

=== CERTIFICATIONS & LICENSES ===
- AWS Certified Cloud Practitioner (2025)
- Oracle Certified Associate Java Programmer
"""
        result = self.detector.detect_sections(resume_text)

        # Verify populated sections
        self.assertIn("Priya Patel", result.sections["contact"])
        self.assertIn("B.E. Information Technology", result.sections["education"])
        self.assertIn("CloudTech Solutions", result.sections["internships"])
        self.assertIn("Distributed Task Queue", result.sections["projects"])
        self.assertIn("Python, Go, Docker", result.sections["skills"])
        self.assertIn("AWS Certified Cloud Practitioner", result.sections["certifications"])

        # Verify core confidence (4/4 core sections: edu, internships, projects, skills = 1.0)
        self.assertEqual(result.metrics.parsing_confidence, 1.0)
        self.assertEqual(result.metrics.detected_sections_count, 6)  # contact, edu, intern, proj, skills, cert

    def test_experienced_student_resume_fixture(self):
        resume_text = """
Rohan Verma
rohan.verma@example.com

PROFESSIONAL SUMMARY
Results-driven software engineer with experience building scalable web applications.

WORK EXPERIENCE
Junior Software Developer | FinTech Labs (Jan 2024 - Present)
- Engineered real-time payments microservice handling 5,000 req/sec

MAJOR PROJECTS
Crypto Analytics Dashboard
- Implemented WebSockets pipeline for real-time orderbook feeds

CORE COMPETENCIES
Languages: Java, Python, TypeScript
Infrastructure: Docker, Kubernetes, Kafka

AWARDS & ACHIEVEMENTS
- 1st Place at National Smart India Hackathon 2025
- Dean's List for Academic Excellence (4 consecutive semesters)

POSITIONS OF RESPONSIBILITY
- Lead Organizer, HackNIT 2025
"""
        result = self.detector.detect_sections(resume_text)

        self.assertIn("Results-driven software engineer", result.sections["summary"])
        self.assertIn("Junior Software Developer", result.sections["experience"])
        self.assertIn("Crypto Analytics Dashboard", result.sections["projects"])
        self.assertIn("Languages: Java, Python", result.sections["skills"])
        self.assertIn("National Smart India Hackathon", result.sections["achievements"])
        self.assertIn("Lead Organizer, HackNIT 2025", result.sections["positions_of_responsibility"])

        # Core sections present: exp, proj, skills (3/4 = 0.75)
        self.assertEqual(result.metrics.parsing_confidence, 0.75)


class TestEdgeCasesAndPreservation(unittest.TestCase):
    """Verify edge cases: empty strings, unknown sections, unmapped text, single sections."""

    def setUp(self):
        self.detector = RuleBasedSectionDetector()

    def test_empty_input_string(self):
        result = self.detector.detect_sections("")
        self.assertEqual(len(result.sections), 12)
        for val in result.sections.values():
            self.assertEqual(val, "")
        self.assertEqual(result.metrics.total_lines_processed, 0)
        self.assertEqual(result.metrics.detected_sections_count, 0)
        self.assertEqual(result.metrics.parsing_confidence, 0.0)
        self.assertFalse(result.metrics.has_contact_info)

    def test_whitespace_only_input(self):
        result = self.detector.detect_sections("   \n\n\t  \n   ")
        self.assertEqual(len(result.sections), 12)
        self.assertEqual(result.metrics.total_lines_processed, 0)
        self.assertEqual(result.metrics.parsing_confidence, 0.0)

    def test_unknown_content_and_unmapped_sections(self):
        resume_text = """
John Doe
john@example.com

SKILLS
Python, SQL

MY CUSTOM UNMAPPED SECTION
This is some miscellaneous custom text that does not match standard headers.
Hobbies: Chess, Photography.
"""
        result = self.detector.detect_sections(resume_text)

        # Pre-header contact is preserved
        self.assertIn("John Doe", result.sections["contact"])
        # Skills preserved
        self.assertIn("Python, SQL", result.sections["skills"])
        # Unmapped section text is preserved in 'other' or appropriate buffer
        # In our detector, unmapped headers stay in previous section or if matched as other go to other
        # The key guarantee is ZERO TEXT LOSS: all text lines appear in output
        all_text = " ".join(result.sections.values())
        self.assertIn("Chess, Photography", all_text)

    def test_single_section_resume(self):
        resume_text = """
EDUCATION
Bachelor of Science in Physics
University of Delhi
"""
        result = self.detector.detect_sections(resume_text)
        self.assertIn("Bachelor of Science", result.sections["education"])
        self.assertEqual(result.sections["skills"], "")
        self.assertEqual(result.metrics.parsing_confidence, 0.25)  # 1/4 core section

    def test_randomized_section_ordering(self):
        resume_text = """
AWARDS & ACHIEVEMENTS
Best Developer Award 2025

TECHNICAL SKILLS
C++, Python

EDUCATION
IIT Delhi

MAJOR PROJECTS
Autonomous Drone Software
"""
        result = self.detector.detect_sections(resume_text)
        self.assertIn("Best Developer Award", result.sections["achievements"])
        self.assertIn("C++, Python", result.sections["skills"])
        self.assertIn("IIT Delhi", result.sections["education"])
        self.assertIn("Autonomous Drone", result.sections["projects"])
        self.assertEqual(result.metrics.parsing_confidence, 0.75)


class TestExtensibilityAndFactory(unittest.TestCase):
    """Verify factory instantiation, abstract interfaces, and future LLM stubs."""

    def test_factory_returns_rule_based_detector(self):
        detector = get_section_detector("rule_based")
        self.assertIsInstance(detector, RuleBasedSectionDetector)
        self.assertIsInstance(detector, BaseSectionDetector)

    def test_factory_default(self):
        detector = get_section_detector()
        self.assertIsInstance(detector, RuleBasedSectionDetector)

    def test_factory_llm_and_hybrid_stubs(self):
        llm_detector = get_section_detector("llm")
        self.assertIsInstance(llm_detector, LLMSectionDetector)
        with self.assertRaises(NotImplementedError):
            llm_detector.detect_sections("dummy text")

        hybrid_detector = get_section_detector("hybrid")
        self.assertIsInstance(hybrid_detector, HybridSectionDetector)
        with self.assertRaises(NotImplementedError):
            hybrid_detector.detect_sections("dummy text")

    def test_factory_invalid_type(self):
        with self.assertRaises(ValueError):
            get_section_detector("unsupported_engine_xyz")

    def test_service_detect_sections_from_text(self):
        result = detect_sections_from_text("EDUCATION\nHarvard University")
        self.assertIsInstance(result, SectionDetectionResult)
        self.assertIn("Harvard University", result.sections["education"])


def run_tests():
    """Run test suite and output human-readable report."""
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n" + "=" * 60)
        print("ALL PHASE 3.4 RESUME SECTION DETECTION TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "!" * 60)
        print(f"FAILED: {len(result.failures)} failures, {len(result.errors)} errors")
        print("!" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
