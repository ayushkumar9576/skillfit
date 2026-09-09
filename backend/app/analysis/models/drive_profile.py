"""
app/analysis/models/drive_profile.py
--------------------------------------
Foundational Drive Intelligence Profile — the structural schema for all
future Drive Intelligence on the SkillFit platform.

Phase 4.1 — Storage Foundation Only.

Design Rules:
    - Pure standard library dataclasses only.
    - Zero framework dependencies (no SQLAlchemy, FastAPI, Pydantic, or OpenAI).
    - Fully serializable via dataclasses.asdict().
    - All intelligence sections are placeholders (list[Any] / dict[str, Any]).
      Phase 4.3 will replace these with strongly-typed intelligence objects
      once the extraction engines are defined.

Naming Symmetry with Candidate Side:
    CandidateIntelligenceProfile   →  DriveIntelligenceProfile
    CandidateIntelligenceSnapshot  →  DriveIntelligenceSnapshot
    ProfileMetadata                →  DriveProfileMetadata

Phase Roadmap for this file:
    Phase 4.1  — DriveIntelligenceProfile (abstract placeholders)
    Phase 4.3  — Replace list[Any] fields with strongly-typed intelligence objects
    Phase 5    — Consumed by Matching Engine alongside CandidateIntelligenceProfile

Consumed by:
    Phase 4.1: drive_service.py (snapshot storage)
    Phase 4.3: Drive Intelligence Engines
    Phase 5:   Matching Engine (Candidate ↔ Drive)
    APIs:      Recruiter views, admin drive dashboard
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


# ---------------------------------------------------------------------------
# Profile Metadata
# ---------------------------------------------------------------------------


@dataclass
class DriveProfileMetadata:
    """
    Metadata captured at snapshot creation time.

    Records what pipeline version produced this profile and what source
    entity it was derived from. Enables reproducibility and auditability.

    Attributes:
        drive_id:          Integer PK of the source Drive entity.
        snapshot_version:  Schema version of DriveIntelligenceProfile (e.g. "1.0").
        analysis_version:  Pipeline version that produced this snapshot (e.g. "4.3.0").
                           In Phase 4.1 this will be "4.1.0" for manually created
                           foundation snapshots.
        generated_at:      UTC timestamp of snapshot generation.
    """
    drive_id: uuid.UUID
    snapshot_version: str = "1.0"
    analysis_version: str = "4.1.0"
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Drive Metadata
# ---------------------------------------------------------------------------


@dataclass
class DriveMetadata:
    """
    Structured metadata about the drive's role and company context.

    This section stores the normalized, intelligence-ready version of the
    raw fields on the Drive entity. Future extraction engines (Phase 4.3)
    will populate this from a parsed job description.

    Attributes:
        company_name:     Normalized company name.
        role_title:       Normalized role/position title.
        role_category:    Broad role category (e.g. "Software Engineering",
                          "Data Science"). Populated by Phase 4.3.
        location:         Location string. May be "Remote", "Hybrid", etc.
        employment_type:  Employment type (e.g. "Full-time", "Internship").
    """
    company_name: str = ""
    role_title: str = ""
    role_category: str = ""
    location: str = ""
    employment_type: str = ""


# ---------------------------------------------------------------------------
# Drive Intelligence Profile
# ---------------------------------------------------------------------------


@dataclass
class DriveIntelligenceProfile:
    """
    The canonical, unified Drive Intelligence model.

    Phase 4.1: This is the structural foundation. All intelligence sections
    are typed as list[Any] or dict[str, Any] to establish the storage
    architecture without prematurely locking intelligence schemas.

    Phase 4.3 will replace these placeholders with strongly-typed dataclass
    objects (e.g. DriveTechnologyIntelligence, DriveCompetencyIntelligence)
    once the extraction engines are designed.

    Design Invariant (Phase 5 perspective):
        Every field that the Matching Engine will need to compare against a
        CandidateIntelligenceProfile must eventually live here. The structure
        below has been designed from the perspective of future matching
        consumption rather than current implementation convenience.

        technologies      ↔  CandidateIntelligenceProfile.technologies
        competencies      ↔  CandidateIntelligenceProfile.competencies
        signals           ↔  CandidateIntelligenceProfile.engineering_signals

    Attributes:
        metadata:           Normalized drive/role identity fields.
        technologies:       Technology intelligence (placeholder — populated Phase 4.3).
        competencies:       Competency requirements (placeholder — populated Phase 4.3).
        signals:            Hiring signals and role indicators (placeholder — Phase 4.3).
        intelligence_sections: Extension dict for future intelligence modules not
                            yet defined. Allows Phase 4.3+ to attach new named
                            sections without a breaking schema change.
        profile_version:    Schema version string (e.g. "1.0").
    """

    # Structured drive identity — populated at creation time
    metadata: DriveMetadata = field(default_factory=DriveMetadata)

    # Intelligence sections — placeholders for Phase 4.3 extraction engines
    # These will become strongly-typed lists once intelligence objects are designed.
    technologies: List[Any] = field(default_factory=list)
    competencies: List[Any] = field(default_factory=list)
    signals: List[Any] = field(default_factory=list)

    # Extension point: named sections for future intelligence modules
    # Examples of future keys: "difficulty", "interview_focus", "success_signals"
    intelligence_sections: Dict[str, Any] = field(default_factory=dict)

    # Schema version — increment when DriveIntelligenceProfile structure changes
    profile_version: str = "1.0"


# ---------------------------------------------------------------------------
# Drive Intelligence Snapshot (persistence wrapper)
# ---------------------------------------------------------------------------


@dataclass
class DriveIntelligenceSnapshot:
    """
    Persistence wrapper for a DriveIntelligenceProfile.

    Separates domain logic (the profile) from persistence concerns (metadata).
    Stored as a versioned JSONB snapshot in the drive_snapshots table.

    Naming symmetry with CandidateIntelligenceSnapshot.

    Attributes:
        snapshot_id:       UUID of the DriveSnapshotModel row (as string).
        drive_id:          Integer PK of the source Drive entity.
        snapshot_version:  Schema version of DriveIntelligenceProfile (e.g. "1.0").
        analysis_version:  Pipeline version that produced this snapshot.
        generated_at:      UTC timestamp of snapshot generation.
        profile:           The actual DriveIntelligenceProfile domain object.
    """
    snapshot_id: str
    drive_id: uuid.UUID
    snapshot_version: str
    analysis_version: str
    profile: DriveIntelligenceProfile
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
