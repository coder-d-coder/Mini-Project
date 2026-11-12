import re

# Each target role is matched against job titles by keyword.
ROLES = {
    "Backend Developer": ["backend", "python", "django", "flask", "node.js", "java", "software engineer"],
    "Frontend Developer": ["frontend", "front end", "web developer", "ui/ux", "designer"],
    "Full-Stack Developer": ["full stack", "web developer", "software engineer"],
    "Data Analyst": ["data analyst", "bi analyst", "data scientist", "data engineer"],
}


def role_matches(role: str, title: str) -> bool:
    keywords = ROLES.get(role, [])
    clean_title = title.lower().replace("-", " ")
    return any(re.search(r"\b" + re.escape(k) + r"\b", clean_title) for k in keywords)