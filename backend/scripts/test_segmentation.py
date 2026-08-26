import asyncio
from app.services.resume.project_extractor import get_project_extractor
from app.services.resume.internship_extractor import get_internship_extractor
from app.services.resume.certification_extractor import get_certification_extractor

def test_extractors():
    print("Testing Project Extractor...")
    project_text = """
PROJECTS
E-Commerce Platform | React, Node.js | Jan 2023 - Present
• Built a scalable e-commerce platform using React and Node.js.
• Increased sales by 20%.
Personal Portfolio Website | HTML, CSS, JS | Jan 2022 - May 2022
• Designed and developed a personal portfolio website.
• Showcased skills and projects.
    """
    p_extractor = get_project_extractor("rule_based")
    p_result = p_extractor.extract(project_text)
    print(f"Projects found: {p_result.total_projects_count}")
    for p in p_result.projects:
        print(f" - {p.title}")

    print("\nTesting Internship Extractor...")
    internship_text = """
EXPERIENCE
Software Engineer Intern | Google | May 2023 - Aug 2023
• Developed features for Google Maps.
• Improved performance by 15%.
Data Science Intern | Meta | Jan 2023 - Apr 2023
• Analyzed user behavior data.
• Built predictive models.
    """
    i_extractor = get_internship_extractor("rule_based")
    i_result = i_extractor.extract(internship_text)
    print(f"Internships found: {i_result.total_internships_count}")
    for i in i_result.internships:
        print(f" - {i.role} at {i.organization}")

    print("\nTesting Certification Extractor Case A...")
    certification_text_A = """
CERTIFICATIONS
Full Stack Web Development
August 2022
Edureka — Certificate Link

Linux for Developers
March 2021
Coursera — Certificate Link
    """
    c_extractor = get_certification_extractor()
    c_result = c_extractor.extract(certification_text_A)
    print(f"Certifications found (Case A): {c_result.total_certifications_count}")
    for c in c_result.certifications:
        print(f" - Title: {c.certification_name} | Provider: {c.issuer}")

    print("\nTesting Certification Extractor Case B...")
    certification_text_B = """
CERTIFICATIONS
AWS Cloud Practitioner
Google Data Analytics Professional Certificate
Microsoft Azure Fundamentals
    """
    c_result_B = c_extractor.extract(certification_text_B)
    print(f"Certifications found (Case B): {c_result_B.total_certifications_count}")
    for c in c_result_B.certifications:
        print(f" - Title: {c.certification_name} | Provider: {c.issuer}")

    print("\nTesting Certification Extractor Case C...")
    certification_text_C = """
CERTIFICATIONS
* AWS Cloud Practitioner
* Google Data Analytics Professional Certificate
* Microsoft Azure Fundamentals
    """
    c_result_C = c_extractor.extract(certification_text_C)
    print(f"Certifications found (Case C): {c_result_C.total_certifications_count}")
    for c in c_result_C.certifications:
        print(f" - Title: {c.certification_name} | Provider: {c.issuer}")

if __name__ == "__main__":
    test_extractors()
