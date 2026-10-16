# Thresholds for Strength and Gap extraction

# A Candidate score >= this threshold is considered strong demonstration
STRENGTH_CANDIDATE_THRESHOLD = 0.8
# A Drive score >= this threshold is considered an expected capability for a strength
STRENGTH_DRIVE_THRESHOLD = 0.5
# Maximum number of strengths to extract
MAX_STRENGTHS = 5

# A Candidate score <= this threshold is considered weak or no evidence
GAP_CANDIDATE_THRESHOLD = 0.2
# A Drive score >= this threshold is considered an expected capability for a gap
GAP_DRIVE_THRESHOLD = 0.25
# Maximum number of gaps to extract
MAX_GAPS = 5

# Severity Mappings based on Drive value
GAP_SEVERITY_THRESHOLDS = {
    1.0: "CRITICAL",
    0.75: "HIGH",
    0.5: "MEDIUM",
    0.25: "LOW"
}
