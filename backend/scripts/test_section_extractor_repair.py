"""
scripts/test_section_extractor_repair.py
----------------------------------------
Comprehensive automated regression test suite for the SkillFit Section Extractor Repair.

Validates:
    - Test Group A: Project Extraction (A1 - A6)
    - Test Group B: Internship Extraction (B1 - B5)
    - Test Group C: Regression & Robustness (C1 - C3)
"""

import os
import sys
import unittest
from typing import List

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.analysis.engines.candidate_intelligence import CandidateIntelligenceAggregator
from app.analysis.models.base import AnalysisEvidence
from app.analysis.models.internship_models import InternshipAnalysisResult, InternshipEvidence
from app.analysis.models.project_models import ProjectAnalysisResult, ProjectEvidence
from app.services.resume.internship_extractor import (
    RuleBasedInternshipExtractor,
    get_internship_extractor,
)
from app.services.resume.project_extractor import (
    RuleBasedProjectExtractor,
    extract_projects_from_text,
    get_project_extractor,
)
from app.services.resume.section_headers import (
    SECTION_HEADER_MAP,
    match_section_header,
    normalize_header_text,
)
from app.services.resume.section_types import ResumeSection


class TestGroupAProjectExtraction(unittest.TestCase):
    """Test Group A — Project Extraction Precision and Boundary Control."""

    def setUp(self):
        self.extractor = RuleBasedProjectExtractor()

    def test_a1_multiple_real_projects_clean_metadata(self):
        """
        Test A1: Multiple real projects with pipe-delimited metadata.
        Titles must NOT contain concatenated dates or link badges.
        """
        raw_text = """
PROJECTS
Kapitl-AutonomousIPOInvestmentPlatform|Live|GitHub Aug2026–Sep2026
FastAPI, Next.js, PostgreSQL, Redis, Celery, ClaudeAI
• Architected an autonomous IPO platform managing 10+ demat accounts.
• Eliminated 85% of manual IPO workflow effort via MILP-based fund optimizer.

JaduiPlacement–AICareerCoach|Live|GitHub May2026–Jun2026
Next.js14, FastAPI, Supabase, PostgreSQL, Gemini
• Architected a full-stack agentic career platform with 14 pages.
• Engineered an AI interview pipeline using Gemini with provider fallback.

PROTECTOS–SecureFileManagementSystem|Live|GitHub Mar2026–Apr2026
React.js, FastAPI, SQLModel, SQLite, AES-256-GCM
• Implemented server-side AES-256-GCM file encryption.
• Deployed a multi-layer upload security pipeline.

EDUCATION
B.Tech Computer Science
"""
        result = self.extractor.extract(raw_text)
        self.assertEqual(len(result.projects), 3)

        titles = [p.title for p in result.projects]
        self.assertEqual(titles[0], "Kapitl-AutonomousIPOInvestmentPlatform")
        self.assertEqual(titles[1], "JaduiPlacement–AICareerCoach")
        self.assertEqual(titles[2], "PROTECTOS–SecureFileManagementSystem")

        # Verify badges and dates are stripped from titles
        for p in result.projects:
            self.assertNotIn("Live", p.title)
            self.assertNotIn("GitHub", p.title)
            self.assertNotIn("2026", p.title)

        # Verify inline technologies were extracted
        self.assertIn("FastAPI", result.projects[0].technologies)
        self.assertIn("Next.js", result.projects[0].technologies)
        self.assertIn("Next.js14", result.projects[1].technologies)
        self.assertIn("React.js", result.projects[2].technologies)

    def test_a2_description_not_a_new_project(self):
        """
        Test A2: A wrapped sentence in a bullet point must not become a standalone project.
        """
        raw_text = """
PROJECTS
JaduiPlacement–AICareerCoach|Live|GitHub May2026–Jun2026
Next.js14, FastAPI, Supabase, PostgreSQL
• Architected a full-stack agentic career platform with 14 pages across dual role systems (Student+Admin), backed by 7 modular
FastAPI services handling resume intelligence, mock interviews, GitHub analytics, PR review, and AI mentorship
• Engineered an AI interview pipeline using Gemini with provider fallback logic.

EDUCATION
B.Tech Computer Science
"""
        result = self.extractor.extract(raw_text)
        self.assertEqual(len(result.projects), 1)
        project = result.projects[0]
        self.assertEqual(project.title, "JaduiPlacement–AICareerCoach")

        # The wrapped sentence must be appended to the first bullet highlight
        combined_highlight = " ".join(project.highlights)
        self.assertIn("FastAPI services handling resume intelligence", combined_highlight)
        self.assertEqual(len(project.highlights), 2)

    def test_a3_section_headings_are_not_projects(self):
        """
        Test A3: Section headings such as HACKATHONS and TRAINING must not appear as project records.
        """
        raw_text = """
PROJECTS
Smart Campus Navigation System | HTML, CSS, JavaScript, DSA Jun 2026 - Jul 2026
• Developed a web-based campus navigation system to help students locate academic blocks.
• Integrated interactive campus maps and DSA-based route representation.

HACKATHONS
Amazon Prompt Builder 2025 Feb 2025
• Secured 4th position by developing an Emergency Evacuation System.

TRAINING
LetsUpgrade (Edtech Company) Sep 2025 - Dec 2025
Student Ambassador
• Promoted LetsUpgrade learning initiatives across the student community.

CERTIFICATES
AI Fundamentals - Google | Coursera May 2026
"""
        result = self.extractor.extract(raw_text)
        titles = [p.title.upper() for p in result.projects]
        self.assertNotIn("HACKATHONS", titles)
        self.assertNotIn("TRAINING", titles)
        self.assertNotIn("STUDENT AMBASSADOR", titles)
        self.assertEqual(len(result.projects), 1)
        self.assertEqual(result.projects[0].title, "Smart Campus Navigation System")

    def test_a4_ambiguous_entry_preservation(self):
        """
        Test A4: Ambiguous entries like 'Multithreading Systems' must be evaluated
        using contextual technical evidence (tech stack, metrics) rather than rejected on title alone.
        """
        raw_text = """
PROJECTS
Multithreading Systems | C, POSIX Threads, Operating Systems Feb 2026 - Apr 2026
• Developed a multithreaded application to demonstrate concurrent execution and core operating-system concepts.
• Implemented thread creation, concurrent execution, synchronization, and shared-resource management using C and POSIX threads.
• Achieved approximately 35% reduction in execution time compared with sequential execution while maintaining synchronized access to shared resources.

EDUCATION
College of Engineering
"""
        result = self.extractor.extract(raw_text)
        self.assertEqual(len(result.projects), 1)
        project = result.projects[0]
        self.assertEqual(project.title, "Multithreading Systems")
        self.assertIn("C", project.technologies)
        self.assertIn("POSIX Threads", project.technologies)
        self.assertEqual(len(project.highlights), 3)

    def test_a5_extracurricular_role_rejected_from_projects(self):
        """
        Test A5: Extracurricular/leadership roles (e.g. Student Ambassador) lacking technical
        project substance must NOT be extracted as projects.
        """
        raw_text = """
PROJECTS
Student Ambassador
• Represented the organization in student outreach events.
• Guided incoming freshmen during orientation week.

Smart Campus Navigation System | HTML, CSS, JavaScript
• Developed campus map routing tool.

EDUCATION
University
"""
        result = self.extractor.extract(raw_text)
        titles = [p.title for p in result.projects]
        self.assertNotIn("Student Ambassador", titles)
        self.assertEqual(len(result.projects), 1)
        self.assertEqual(result.projects[0].title, "Smart Campus Navigation System")

    def test_a6_formatting_variation(self):
        """
        Test A6: Formatting variations (missing dates, missing links, unbulleted lines, varied delimiters).
        """
        raw_text = """
PROJECTS
Distributed Cache Service
Built a distributed LRU cache service with consistent hashing and replication.
• Implemented consistent hashing ring with 256 virtual nodes per server.
• Added Raft consensus for leader election and state synchronization.

Inventory Tracker - Vue.js, Node.js, SQLite
• Single page application for small store warehouse tracking.
• Enabled real-time barcode scanning.

EDUCATION
University
"""
        result = self.extractor.extract(raw_text)
        self.assertEqual(len(result.projects), 2)
        self.assertEqual(result.projects[0].title, "Distributed Cache Service")
        self.assertEqual(result.projects[1].title, "Inventory Tracker")
        self.assertIn("Vue.js", result.projects[1].technologies)


class TestGroupBInternshipExtraction(unittest.TestCase):
    """Test Group B — Internship Detection Precision and Schema Conformance."""

    def setUp(self):
        self.extractor = RuleBasedInternshipExtractor()

    def test_b1_internship_under_experience_heading(self):
        """
        Test B1: Internship role under a general EXPERIENCE heading without separate INTERNSHIPS header.
        """
        raw_text = """
EXPERIENCE
Backend Engineering Intern | TechNova Solutions | Jun 2024 - Aug 2024
• Designed RESTful microservices using Go and PostgreSQL.
• Wrote comprehensive unit and integration tests achieving 90% code coverage.

PROJECTS
Smart App | React
• Developed mobile app.
"""
        result = self.extractor.extract(raw_text)
        self.assertEqual(len(result.internships), 1)
        internship = result.internships[0]
        self.assertEqual(internship.organization, "TechNova Solutions")
        self.assertEqual(internship.role, "Backend Engineering Intern")
        self.assertIn("Jun 2024 - Aug 2024", internship.duration)
        self.assertEqual(len(internship.achievements), 2)

    def test_b2_internship_heading_variants(self):
        """
        Test B2: Test recognized heading variants (WORK EXPERIENCE & INTERNSHIPS, SUMMER INTERNSHIPS).
        """
        raw_text = """
WORK EXPERIENCE & INTERNSHIPS
Virtuoso Netsoft Pvt. Ltd. | Technical Department Intern | Jun 2026 - Aug 2026
• Developed responsive user interface components with Angular.
• Integrated REST APIs with backend services.

EDUCATION
University
"""
        result = self.extractor.extract(raw_text)
        self.assertEqual(len(result.internships), 1)
        internship = result.internships[0]
        self.assertEqual(internship.organization, "Virtuoso Netsoft Pvt. Ltd.")
        self.assertEqual(internship.role, "Technical Department Intern")
        self.assertIn("Jun 2026 - Aug 2026", internship.duration)

    def test_b3_missing_optional_metadata(self):
        """
        Test B3: Internship with missing optional metadata (no links, no location, incomplete date).
        Must be preserved without fabricating missing fields.
        """
        raw_text = """
INTERNSHIPS
Acme Labs
Software Intern
• Automated regression test suite for internal developer tools.

PROJECTS
CLI Utility | Rust
• Built command line tool.
"""
        result = self.extractor.extract(raw_text)
        self.assertEqual(len(result.internships), 1)
        internship = result.internships[0]
        self.assertEqual(internship.organization, "Acme Labs")
        self.assertEqual(internship.role, "Software Intern")
        self.assertIsNone(internship.duration)
        self.assertIsNone(internship.location)
        self.assertEqual(len(internship.achievements), 1)

    def test_b4_multiline_internship_description_and_swapped_headers(self):
        """
        Test B4: 2-line header layout with Role on Line 1, Company on Line 2 (CV 3 layout),
        and multiline wrapped bullet points.
        """
        raw_text = """
INTERNSHIP
SEP Intern May 2023 - July 2023
JP Morgan Chase & Co.
• Contributed to the advancement of the organization's robust Document Manager web application,
enabling easier and faster navigation to relevant records.
• Improved user experience and productivity by implementing comprehensive row grouping.

Full Stack Web Developer Intern Feb 2022 - Aug 2022
Edureka
• Built two dynamic web applications leveraging the power of MERN stack.
• Automated web data collection through software tools and custom scripts.

PROJECTS
Fkart App | MERN Stack
• Developed e-commerce platform.
"""
        result = self.extractor.extract(raw_text)
        self.assertEqual(len(result.internships), 2)

        int1 = result.internships[0]
        self.assertEqual(int1.organization, "JP Morgan Chase & Co.")
        self.assertEqual(int1.role, "SEP Intern")
        self.assertIn("May 2023 - July 2023", int1.duration)
        self.assertEqual(len(int1.achievements), 2)
        # Verify multiline wrapped bullet point was preserved as single achievement
        self.assertIn("enabling easier and faster navigation", int1.achievements[0])

        int2 = result.internships[1]
        self.assertEqual(int2.organization, "Edureka")
        self.assertEqual(int2.role, "Full Stack Web Developer Intern")
        self.assertIn("Feb 2022 - Aug 2022", int2.duration)
        self.assertEqual(len(int2.achievements), 2)

    def test_b5_end_to_end_intelligence_pipeline_preservation(self):
        """
        Test B5: Verify extracted internships and projects feed cleanly into
        CandidateIntelligenceAggregator and survive profile construction.
        """
        agg = CandidateIntelligenceAggregator()

        # Simulate extracted projects
        p_res = self.extractor.extract("""
INTERNSHIPS
Eventviewz | Frontend Developer Intern | Oct 2025 - Nov 2025 | Remote
• Developed event listing pages and registration workflows.
""")
        self.assertEqual(len(p_res.internships), 1)
        internship = p_res.internships[0]
        self.assertEqual(internship.organization, "Eventviewz")
        self.assertEqual(internship.role, "Frontend Developer Intern")

        # Feed into aggregator (mirrors resume_pipeline.py Stage 6)
        from app.analysis.models.candidate_profile import IntelligenceEvidence, IntelligenceSourceType, WorkplaceExposure
        evidence = IntelligenceEvidence(
            source=IntelligenceSourceType.INTERNSHIP,
            source_id=internship.organization,
            section="internships",
            quote=f"{internship.organization} - {internship.role}",
        )
        agg.add_workplace_exposure([
            WorkplaceExposure(
                exposure_type="production_systems",
                evidence=[evidence],
            )
        ])

        profile = agg.build()
        self.assertEqual(len(profile.workplace_exposure), 1)
        self.assertEqual(profile.workplace_exposure[0].exposure_type, "production_systems")
        self.assertEqual(profile.workplace_exposure[0].evidence[0].quote, "Eventviewz - Frontend Developer Intern")

    def test_b6_training_labeled_internship_experience(self):
        """
        Test B6: Training-as-internships handling across Indian campus formats:
        - SUMMER TRAINING
        - INDUSTRIAL TRAINING
        - TRAINING & INTERNSHIP
        - Generic TRAINING with Trainee role
        - Distinguishing pure courses from internships under TRAINING
        """
        raw_text = """
SUMMER TRAINING
Web Development Trainee | Hewlett Packard Enterprise | Jun 2024 - Jul 2024
• Built REST APIs using Django and PostgreSQL.

INDUSTRIAL TRAINING
Bharat Electronics Limited, Ghaziabad
Embedded Systems Trainee (July 2024 – August 2024)
• Programmed ARM Cortex microcontrollers for radar signal transmission.

TRAINING & INTERNSHIP
Software Engineering Intern | Infosys Springboard   Feb 2024 - May 2024
• Implemented microservices and wrote unit tests.

TRAINING
Summer Intern | National Informatics Centre   May 2024 – July 2024
• Developed government web portal modules using React.
• Complete Python Bootcamp (Udemy, 2023)
• AWS Certified Cloud Practitioner (2024)
"""
        result = self.extractor.extract(raw_text)
        self.assertEqual(len(result.internships), 4)

        orgs = [i.organization for i in result.internships]
        self.assertIn("Hewlett Packard Enterprise", orgs)
        self.assertIn("Bharat Electronics Limited", orgs)
        self.assertIn("Infosys Springboard", orgs)
        self.assertIn("National Informatics Centre", orgs)

        # Pure certificates/courses must NOT be extracted as fake internships
        self.assertNotIn("Complete Python Bootcamp", orgs)
        self.assertNotIn("AWS Certified Cloud Practitioner", orgs)


class TestGroupCRegressionAndRobustness(unittest.TestCase):
    """Test Group C — Generalization, Edge Cases, and Real Resume Fixtures."""

    def test_c1_edge_cases_and_empty_inputs(self):
        proj_ext = get_project_extractor("rule_based")
        int_ext = get_internship_extractor("rule_based")

        # Empty / whitespace
        self.assertEqual(len(proj_ext.extract("").projects), 0)
        self.assertEqual(len(proj_ext.extract("   \n\n  ").projects), 0)
        self.assertEqual(len(int_ext.extract("").internships), 0)
        self.assertEqual(len(int_ext.extract("   \n\n  ").internships), 0)

        # Resume with no projects section
        res_no_proj = proj_ext.extract("EDUCATION\nB.Tech\nSKILLS\nPython, C++")
        self.assertEqual(len(res_no_proj.projects), 0)

        # Resume with no internships section
        res_no_int = int_ext.extract("EDUCATION\nB.Tech\nSKILLS\nPython, C++")
        self.assertEqual(len(res_no_int.internships), 0)

    def test_c2_multiple_experience_sections_captured(self):
        """
        Verify that if a resume contains both an INTERNSHIPS and a separate EXPERIENCE section,
        all blocks are captured.
        """
        raw_text = """
INTERNSHIPS
Meta Platforms | Software Intern | Jun 2025 - Aug 2025
• Worked on React performance optimization.

PROJECTS
OpenSource Tool | Rust
• Contributed to memory safety analyzer.

EXPERIENCE
Google LLC | Engineering Fellow | Sep 2025 - Dec 2025
• Developed internal telemetry dashboard.

EDUCATION
MIT
"""
        int_ext = get_internship_extractor("rule_based")
        result = int_ext.extract(raw_text)
        self.assertEqual(len(result.internships), 2)
        orgs = [i.organization for i in result.internships]
        self.assertIn("Meta Platforms", orgs)
        self.assertIn("Google LLC", orgs)

    def test_c3_cv1_real_anonymized_fixture(self):
        """
        CV 1 (Ravi Yadav):
        Must extract exactly 3 projects (Kapitl, JaduiPlacement, PROTECTOS).
        Must NOT extract 'FastAPI services handling...' as a project.
        Must extract exactly 2 internships (LearnDevs and Eventviewz).
        """
        raw_text = """
INTERNSHIPS
LearnDevs Remote|Python,Playwright,MySQL,React.js,Next.js,TailwindCSS Feb2026 Apr2026
SoftwareEngineeringIntern
• AutomatedcoursedatacollectionusingaPlaywright-basedPythonscraperwithscheduledcronjobs,maintainingaMySQL
backendof20,000+coursesandeliminatingmanualdataentryentirely
• Engineered a full blog system with admin portal, rich-text editor, image upload pipeline, and SEO-optimized slug routing
enablingnon-technicaladminstopublishandmanagecontentindependently
Eventviewz Jalandhar,Punjab,India|React.js,Next.js,TailwindCSS Oct2025 Nov2025
FrontendDeveloperIntern
• Developedeventlistingpages,detailviews,andend-to-endregistrationworkflowsaspartofaplatformserving10,000+users
across15+liveevents
• Designedandshippedtheadmininterfaceforeventmanagement,enablingoperatorstocreate,update,andmonitoreventswith
real-timevisibility
PROJECTS
Kapitl-AutonomousIPOInvestmentPlatform|Live|GitHub Aug2026 Sep2026
FastAPI,Next.js,PostgreSQL,Redis,Celery,ClaudeAI,AngelOneSmartAPI
• ArchitectedanautonomousIPOplatformmanaging10+demataccounts multi-agentAIpipeline(Claude+Gemini)forDRHP
scoringandGMPsentimentanalysis,increasingallotmentprobabilityby40%
• Eliminated 85% of manual IPO workflow effort via MILP-based fund optimizer (PuLP) enforcing SEBI category constraints,
ASBAlockconflictdetection,andCeleryBeatautomation reducingcapitalidletimeby35%
JaduiPlacement AICareerCoach|Live|GitHub May2026 Jun2026
Next.js14,FastAPI,Supabase,PostgreSQL,Gemini,Groq,Vapi
• Architectedafull-stackagenticcareerplatformwith14pagesacrossdualrolesystems(Student+Admin),backedby7modular
FastAPIserviceshandlingresumeintelligence,mockinterviews,GitHubanalytics,PRreview,andAImentorship
• Engineered an AI interview pipeline using Gemini with provider fallback logic, delivering adaptive question generation and
per-answerscoring integratedVapiforreal-timevoiceinterviewsessionswithliveAIfeedback
PROTECTOS SecureFileManagementSystem|Live|GitHub Mar2026 Apr2026
React.js(TypeScript),FastAPI,SQLModel,SQLite,AES-256-GCM
• Implemented server-side AES-256-GCM file encryption with nonce-prepended ciphertext and automatic auth tag verification
ondecryption invalidkeyorcorruptedfiletriggersintegrityfailurebeforeanydataisexposed
• Deployedamulti-layeruploadsecuritypipeline:malwaresignaturescanning(PEheaders,ELF,EICAR,OLEmacros,embedded
JS/PHP),dangerousextensionblocking,filenamesanitization,andautomaticquarantinewithdownloadandsharingdisabledfor
flaggedfiles
CERTIFICATES
45-DaySummerTrainingPrograminDataStructures&Algorithms
"""
        proj_res = extract_projects_from_text(raw_text)
        self.assertEqual(len(proj_res.projects), 3)
        self.assertEqual(proj_res.projects[0].title, "Kapitl-AutonomousIPOInvestmentPlatform")
        self.assertIn("JaduiPlacement", proj_res.projects[1].title)
        self.assertIn("PROTECTOS", proj_res.projects[2].title)

        int_res = get_internship_extractor("rule_based").extract(raw_text)
        self.assertEqual(len(int_res.internships), 2)
        self.assertEqual(int_res.internships[0].organization, "LearnDevs")
        self.assertEqual(int_res.internships[0].role, "SoftwareEngineeringIntern")
        self.assertEqual(int_res.internships[1].organization, "Eventviewz")
        self.assertEqual(int_res.internships[1].role, "FrontendDeveloperIntern")

    def test_c4_cv2_real_anonymized_fixture(self):
        """
        CV 2 (Shreyash Taparia):
        Must extract exactly 3 projects (Smart Campus Navigation System, News Clustering System, Multithreading Systems).
        Must NOT extract HACKATHONS, TRAINING, or Student Ambassador as projects.
        """
        raw_text = """
PROJECTS
Smart Campus Navigation System | HTML, CSS, JavaScript, DSA Jun 2026 - Jul 2026
• Developed a web-based campus navigation system to help students locate academic blocks.
• Integrated interactive campus maps, department-specific navigation, and DSA-based route representation.
• Successfully mapped 50+ campus locations and implemented navigation across 10+ major routes.
News Clustering System | Python, NLP, Machine Learning, Scikit-Learn Apr 2026 - Jun 2026
• Developed an NLP-based system to automatically group news articles with similar content and topics.
• Preprocessed textual data, performed feature extraction using TF-IDF, and applied clustering algorithms.
• Achieved a Silhouette Score of 0.72, indicating well-separated and meaningful news clusters.
Multithreading Systems | C, POSIX Threads, Operating Systems Feb 2026 - Apr 2026
• Developed a multithreaded application to demonstrate concurrent execution and core operating-system concepts.
• Implemented thread creation, concurrent execution, synchronization, and shared-resource management.
• Achieved approximately 35% reduction in execution time compared with sequential execution.
HACKATHONS
Amazon Prompt Builder 2025 Feb 2025
• Secured 4th position by developing an Emergency Evacuation System.
TRAINING
LetsUpgrade (Edtech Company) Sep 2025 - Dec 2025
Student Ambassador
• Promoted LetsUpgrade learning initiatives across the student community.
CERTIFICATES
Data Analytics Job Simulation
"""
        proj_res = extract_projects_from_text(raw_text)
        self.assertEqual(len(proj_res.projects), 3)
        self.assertEqual(proj_res.projects[0].title, "Smart Campus Navigation System")
        self.assertEqual(proj_res.projects[1].title, "News Clustering System")
        self.assertEqual(proj_res.projects[2].title, "Multithreading Systems")

        # Verify no section headers or ambassador roles leaked
        titles = [p.title.upper() for p in proj_res.projects]
        self.assertNotIn("HACKATHONS", titles)
        self.assertNotIn("TRAINING", titles)
        self.assertNotIn("STUDENT AMBASSADOR", titles)


if __name__ == "__main__":
    unittest.main()
