"""
app/matching/services/eligibility_service.py
--------------------------------------------
Academic Eligibility Evaluation Service for Placement Drives.

Evaluates student academic profile (CGPA, active backlogs, branch, graduation year)
against Drive Intelligence qualifications extracted from the Job Description.

Principles:
    - Non-destructive: Ineligible drives are NOT excluded; they are surfaced
      with is_eligible=False and transparent, student-facing explanations.
    - Deterministic: Evaluates strictly against defined QualificationType &
      QualificationOperator rules.
    - Evidence-grounded: Only mandatory qualifications (is_mandatory=True)
      cause is_eligible to become False.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from app.core.enums import QualificationOperator, QualificationType
from app.models.drive_snapshot import DriveSnapshotModel
from app.models.student import Student

logger = logging.getLogger(__name__)

# Common branch synonyms / acronyms for flexible matching
_BRANCH_SYNONYMS: Dict[str, List[str]] = {
    "cse": ["computer science", "computer engineering", "cs", "computer science and engineering"],
    "it": ["information technology", "info tech"],
    "ece": ["electronics", "electronics and communication", "communication engineering", "electronics and communication engineering"],
    "eee": ["electrical", "electrical engineering", "electrical and electronics", "electrical and electronics engineering"],
    "me": ["mechanical", "mechanical engineering", "mech"],
    "ce": ["civil", "civil engineering"],
    "ds": ["data science", "ai", "artificial intelligence", "ai & ds", "ai and data science"],
}


def _normalize_branch(branch: str) -> str:
    # Normalize punctuation and full aliases, never substrings such as CE in ECE.
    value = re.sub(r"[^a-z0-9]+", " ", branch.lower().replace("&", " and ").replace(".", ""))
    return " ".join(value.split())


_BRANCH_ALIASES = {
    _normalize_branch(alias): key
    for key, synonyms in _BRANCH_SYNONYMS.items()
    for alias in [key, *synonyms]
}


def _branch_matches(student_branch: str, allowed_branches: List[str]) -> bool:
    """
    Check if the student's branch matches any branch in the allowed list,
    accounting for abbreviations, punctuation, and common synonyms.
    """
    if not student_branch or not allowed_branches:
        return False

    s_clean = _normalize_branch(student_branch)
    student_key = _BRANCH_ALIASES.get(s_clean, s_clean)
    for allowed in allowed_branches:
        a_clean = _normalize_branch(str(allowed))
        if not a_clean:
            continue
        if student_key == _BRANCH_ALIASES.get(a_clean, a_clean):
            return True

    return False


class EligibilityService:
    """
    Evaluates academic eligibility of a student against drive snapshot qualifications.
    """

    @classmethod
    def evaluate_eligibility(
        cls,
        student: Student,
        snapshot: Optional[Union[DriveSnapshotModel, Dict[str, Any]]],
    ) -> Tuple[bool, List[str]]:
        """
        Evaluate student academic profile against snapshot qualifications.

        Returns:
            Tuple[bool, List[str]]: (is_eligible, eligibility_reasons)
            - is_eligible: True if all mandatory qualifications are met.
            - eligibility_reasons: List of clear explanations for any failed criteria.
        """
        if not snapshot:
            return True, []

        if isinstance(snapshot, DriveSnapshotModel):
            payload = snapshot.intelligence_payload or {}
        elif isinstance(snapshot, dict):
            payload = snapshot
        else:
            return True, []

        qualifications: List[Dict[str, Any]] = payload.get("qualifications", [])
        if not qualifications:
            return True, []

        reasons: List[str] = []

        for q in qualifications:
            q_type = q.get("qualification_type")
            operator = q.get("operator")
            numeric_val = q.get("numeric_value")
            allowed_vals = q.get("allowed_values") or []
            is_mandatory = q.get("is_mandatory", True)

            # Convert enum objects to strings if needed
            if hasattr(q_type, "value"):
                q_type = q_type.value
            if hasattr(operator, "value"):
                operator = operator.value

            q_type_str = str(q_type).upper() if q_type else ""
            op_str = str(operator).upper() if operator else ""

            # Only mandatory criteria disqualify the candidate
            if not is_mandatory:
                continue

            # -------------------------------------------------------------------
            # 1. CGPA Cutoff
            # -------------------------------------------------------------------
            if q_type_str in ("CGPA", QualificationType.cgpa.value):
                if student.cgpa is None:
                    reasons.append(
                        f"Minimum CGPA cutoff ({numeric_val}) cannot be verified (CGPA not provided in profile)"
                    )
                elif numeric_val is not None:
                    s_cgpa = float(student.cgpa)
                    req_cgpa = float(numeric_val)
                    if op_str in ("GTE", ">=") and s_cgpa < req_cgpa:
                        reasons.append(
                            f"CGPA {s_cgpa:.2f} is below the required cutoff of {req_cgpa:.2f}"
                        )
                    elif op_str in ("LTE", "<=") and s_cgpa > req_cgpa:
                        reasons.append(
                            f"CGPA {s_cgpa:.2f} exceeds the maximum limit of {req_cgpa:.2f}"
                        )
                    elif op_str in ("EQ", "==") and abs(s_cgpa - req_cgpa) > 1e-3:
                        reasons.append(
                            f"CGPA {s_cgpa:.2f} does not match required CGPA of {req_cgpa:.2f}"
                        )

            # -------------------------------------------------------------------
            # 2. Active Backlogs Rule
            # -------------------------------------------------------------------
            elif q_type_str in ("BACKLOG_RULE", QualificationType.backlog_rule.value):
                if student.active_backlogs is None:
                    reasons.append(
                        "Active backlog status is not specified in your profile"
                    )
                else:
                    s_backlogs = int(student.active_backlogs)
                    max_backlogs = int(numeric_val) if numeric_val is not None else 0
                    if op_str in ("LTE", "<=") and s_backlogs > max_backlogs:
                        reasons.append(
                            f"Drive permits at most {max_backlogs} active backlog(s), but you currently have {s_backlogs}"
                        )
                    elif op_str in ("EQ", "==") and s_backlogs != max_backlogs:
                        reasons.append(
                            f"Drive requires {max_backlogs} active backlog(s), but you have {s_backlogs}"
                        )

            # -------------------------------------------------------------------
            # 3. Branch / Department Eligibility
            # -------------------------------------------------------------------
            elif q_type_str in ("BRANCH", QualificationType.branch.value):
                if not student.branch:
                    reasons.append("Branch/Department is not specified in your profile")
                elif allowed_vals:
                    matched = _branch_matches(student.branch, allowed_vals)
                    if op_str in ("IN", "EQ", "==") and not matched:
                        branches_label = ", ".join(str(b) for b in allowed_vals)
                        reasons.append(
                            f"Drive is restricted to [{branches_label}], but your branch is {student.branch}"
                        )
                    elif op_str in ("NOT_IN", "!=") and matched:
                        reasons.append(
                            f"Students from {student.branch} branch are not eligible for this drive"
                        )

            # -------------------------------------------------------------------
            # 4. Graduation Year / Batch
            # -------------------------------------------------------------------
            elif q_type_str in ("GRADUATION_YEAR", QualificationType.graduation_year.value):
                if not student.graduation_year:
                    reasons.append("Graduation year is not specified in your profile")
                else:
                    s_gy = int(student.graduation_year)
                    if allowed_vals:
                        years_allowed = []
                        for val in allowed_vals:
                            try:
                                years_allowed.append(int(val))
                            except (ValueError, TypeError):
                                pass
                        if not years_allowed or op_str not in ("IN", "EQ", "==", "NOT_IN", "!="):
                            reasons.append("Graduation year requirement could not be verified")
                        elif op_str in ("NOT_IN", "!=") and s_gy in years_allowed:
                            reasons.append(f"Students graduating in {s_gy} are not eligible for this drive")
                        elif op_str in ("IN", "EQ", "==") and s_gy not in years_allowed:
                            years_label = ", ".join(str(y) for y in years_allowed)
                            reasons.append(
                                f"Drive is open to [{years_label}] batch only, but your graduation year is {s_gy}"
                            )
                    elif numeric_val is not None:
                        req_year = int(numeric_val)
                        if op_str in ("EQ", "==") and s_gy != req_year:
                            reasons.append(
                                f"Drive is open to {req_year} batch only, but your graduation year is {s_gy}"
                            )
                        elif op_str in ("GTE", ">=") and s_gy < req_year:
                            reasons.append(
                                f"Minimum graduation year is {req_year}, but your graduation year is {s_gy}"
                            )
                        elif op_str in ("LTE", "<=") and s_gy > req_year:
                            reasons.append(
                                f"Maximum graduation year is {req_year}, but your graduation year is {s_gy}"
                            )

        is_eligible = len(reasons) == 0
        return is_eligible, reasons
