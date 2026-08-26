import sys
from app.services.resume.certification_extractor import get_certification_extractor

def run_test(case_name, text, expected_count=None):
    print(f"\n--- {case_name} ---")
    extractor = get_certification_extractor()
    result = extractor.extract(text)
    print(f"Certifications found: {result.total_certifications_count}")
    
    if expected_count is not None and result.total_certifications_count != expected_count:
        print(f"!!! FAILED: Expected {expected_count} but got {result.total_certifications_count}")
        
    for i, c in enumerate(result.certifications, 1):
        # We also want to see what evidence got attached
        ev_lines = [e.evidence_text for e in c.evidences]
        print(f"  {i}. Title: {c.certification_name}")
        print(f"     Provider: {c.issuer}")
        print(f"     Evidence block: {ev_lines}")
    
    return result

def main():
    case1 = """
CERTIFICATIONS

Full Stack Web Development
August 2022
Edureka — Certificate Link

Linux for Developers
March 2021
Coursera — Certificate Link
"""

    case2 = """
CERTIFICATIONS
AWS Certified Cloud Practitioner
Google Data Analytics Professional Certificate
Microsoft Azure Fundamentals
"""

    case3 = """
CERTIFICATIONS
AWS Certified Cloud Practitioner
Amazon Web Services

Google Data Analytics Professional Certificate
Coursera
"""

    case4 = """
CERTIFICATIONS
Machine Learning Specialization
Coursera
2024

Deep Learning Specialization
Coursera
2024
"""

    case5 = """
CERTIFICATIONS
• AWS Certified Cloud Practitioner
• Google Data Analytics Professional Certificate
• Microsoft Azure Fundamentals
"""

    case6 = """
CERTIFICATIONS
1. AWS Certified Cloud Practitioner
2. Google Data Analytics Professional Certificate
3. Microsoft Azure Fundamentals
"""

    case7 = """
CERTIFICATIONS
AWS Certified Cloud Practitioner
AWS Certified Cloud Practitioner
"""

    case8 = """
CERTIFICATIONS
"""

    # Generate 30 certifications
    case9 = "CERTIFICATIONS\n"
    for i in range(1, 31):
        case9 += f"Certification Number {i}\n"

    # Case 10 is identical to Case 1 effectively, but we add assertions
    
    res1 = run_test("Case 1: Multi-line certificate with provider and link", case1, 2)
    run_test("Case 2: Dense certification list with no blank lines", case2, 3)
    run_test("Case 3: Provider on separate line", case3, 2)
    run_test("Case 4: Date on separate line", case4, 2)
    run_test("Case 5: Bulleted certifications", case5, 3)
    run_test("Case 6: Numbered certifications", case6, 3)
    run_test("Case 7: Duplicate certifications", case7, 1)
    run_test("Case 8: Empty certification section", case8, 0)
    run_test("Case 9: More than MAX_CERTIFICATIONS_PER_RESUME", case9, 25)
    
    print("\n--- Case 10: Regression test for the original bug ---")
    titles = [c.certification_name for c in res1.certifications]
    print(f"Titles found: {titles}")
    if any("Edureka" in t or "Coursera" in t for t in titles):
        print("!!! FAILED: Provider lines became standalone certifications.")
    else:
        print("Assertion Passed: Metadata lines did NOT become standalone certifications.")

if __name__ == "__main__":
    main()
