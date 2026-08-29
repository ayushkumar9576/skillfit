"""
app/analysis/serialization/profile_serializer.py
------------------------------------------------
Serializer for CandidateIntelligenceProfile dataclasses.

Handles round-trip conversion:
CandidateIntelligenceProfile -> Dict (JSON-ready) -> CandidateIntelligenceProfile
"""

import json
from typing import Any, Dict
from datetime import datetime, timezone

from pydantic import TypeAdapter
from app.analysis.models.candidate_profile import CandidateIntelligenceProfile

# Current schema version
SCHEMA_VERSION = "1.0"
# Hardcoded for now, ideally passed in dynamically or read from config
ANALYSIS_VERSION = "4.0.0"

_profile_adapter = TypeAdapter(CandidateIntelligenceProfile)

class ProfileSerializer:
    @staticmethod
    def to_snapshot_payload(profile: CandidateIntelligenceProfile, analysis_version: str = ANALYSIS_VERSION) -> Dict[str, Any]:
        """
        Serialize a CandidateIntelligenceProfile into the standard JSON wrapper.
        """
        
        profile_data = _profile_adapter.dump_python(profile, mode='json')
        
        return {
            "schema_version": SCHEMA_VERSION,
            "analysis_version": analysis_version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "profile": profile_data
        }

    @staticmethod
    def from_snapshot_payload(payload: Dict[str, Any]) -> CandidateIntelligenceProfile:
        """
        Deserialize a JSON wrapper payload back into a CandidateIntelligenceProfile.
        """
        # Validate schema version
        schema_version = payload.get("schema_version")
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema version: {schema_version}")
            
        profile_dict = payload.get("profile", {})
        
        return _profile_adapter.validate_python(profile_dict)


