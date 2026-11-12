from app.database import SessionLocal
from app.models import Job, Skill

SKILLS = [
    "Python", "SQL", "MySQL", "JavaScript", "HTML", "CSS", "FastAPI", "Django",
    "Flask", "React", "Node.js", "Java", "Spring Boot", "Git", "Docker", "AWS",
    "Linux", "REST APIs", "Pandas", "NumPy", "Machine Learning", "Data Analysis",
    "Excel", "Power BI", "Tableau", "Statistics", "Communication", "Figma",
    "Testing", "Kubernetes",
]

# (title, company, location, min_experience, salary_min, salary_max, skills, description)
JOBS = [
    ("Junior Python Developer", "CodeNest", "Remote", 0, 300000, 500000,
     ["Python", "SQL", "Git", "REST APIs"], "Build and maintain small Python services."),
    ("Backend Developer (FastAPI)", "ApiForge", "Bengaluru", 2, 700000, 1200000,
     ["Python", "FastAPI", "MySQL", "REST APIs", "Docker"], "Design and ship REST APIs."),
    ("Full Stack Developer", "WebWorks", "Pune", 2, 700000, 1300000,
     ["JavaScript", "HTML", "CSS", "React", "Node.js", "SQL"], "Work on both frontend and backend."),
    ("Frontend Developer", "PixelPath", "Remote", 1, 500000, 900000,
     ["HTML", "CSS", "JavaScript", "React", "Git"], "Build responsive user interfaces."),
    ("Data Analyst", "InsightIQ", "Delhi", 1, 400000, 800000,
     ["SQL", "Excel", "Data Analysis", "Power BI", "Statistics"], "Turn data into reports."),
    ("Data Scientist", "DataLeaf", "Hyderabad", 3, 1200000, 2200000,
     ["Python", "Pandas", "NumPy", "Machine Learning", "Statistics", "SQL"], "Build predictive models."),
    ("Machine Learning Engineer", "NeuralNest", "Bengaluru", 3, 1400000, 2500000,
     ["Python", "Machine Learning", "Docker", "AWS", "Git"], "Deploy ML models to production."),
    ("Java Backend Developer", "EnterpriseHub", "Mumbai", 2, 800000, 1500000,
     ["Java", "Spring Boot", "MySQL", "REST APIs", "Git"], "Develop enterprise backend services."),
    ("DevOps Engineer", "CloudBridge", "Gurugram", 3, 1200000, 2200000,
     ["Linux", "Docker", "Kubernetes", "AWS", "Git"], "Automate deployments and infrastructure."),
    ("QA Automation Engineer", "TestRight", "Pune", 2, 600000, 1100000,
     ["Python", "Testing", "Git", "REST APIs"], "Write automated tests for APIs."),
    ("Django Developer", "WebCraft", "Remote", 1, 500000, 1000000,
     ["Python", "Django", "SQL", "HTML", "CSS"], "Build web apps with Django."),
    ("Flask Developer Intern", "StartupSpark", "Delhi", 0, 150000, 250000,
     ["Python", "Flask", "HTML", "CSS", "Git"], "Learn and build with Flask."),
    ("BI Analyst", "BoardRoom Analytics", "Mumbai", 2, 600000, 1100000,
     ["SQL", "Tableau", "Power BI", "Excel", "Communication"], "Create dashboards for stakeholders."),
    ("Web Developer Trainee", "BrightSites", "Remote", 0, 200000, 350000,
     ["HTML", "CSS", "JavaScript", "Git"], "Entry-level web development."),
    ("Cloud Engineer", "SkyOps", "Hyderabad", 2, 900000, 1600000,
     ["AWS", "Linux", "Docker", "Python"], "Manage cloud infrastructure."),
    ("Node.js Developer", "ServerSide", "Bengaluru", 2, 700000, 1300000,
     ["JavaScript", "Node.js", "REST APIs", "MySQL", "Git"], "Build scalable Node.js services."),
    ("UI/UX Designer", "DesignDen", "Delhi", 1, 450000, 900000,
     ["Figma", "HTML", "CSS", "Communication"], "Design clean, usable interfaces."),
    ("Database Administrator", "DataVault", "Gurugram", 3, 900000, 1500000,
     ["MySQL", "SQL", "Linux"], "Maintain and tune MySQL databases."),
    ("Data Engineer", "PipelinePro", "Pune", 3, 1100000, 2000000,
     ["Python", "SQL", "Pandas", "AWS", "Docker"], "Build data pipelines."),
    ("Software Engineer", "GenericTech", "Mumbai", 1, 600000, 1100000,
     ["Java", "Python", "SQL", "Git", "Testing"], "General software development."),
]


def seed():
    db = SessionLocal()
    try:
        if db.query(Job).count() > 0:
            print("Jobs already exist. Skipping seed.")
            return

        skill_map = {}
        for name in SKILLS:
            skill = db.query(Skill).filter_by(name=name).first()
            if not skill:
                skill = Skill(name=name)
                db.add(skill)
            skill_map[name] = skill
        db.flush()

        for title, company, location, min_exp, sal_min, sal_max, skill_names, desc in JOBS:
            db.add(Job(
                title=title,
                company=company,
                location=location,
                min_experience=min_exp,
                salary_min=sal_min,
                salary_max=sal_max,
                description=desc,
                skills=[skill_map[n] for n in skill_names],
            ))

        db.commit()
        print(f"Seeded {len(SKILLS)} skills and {len(JOBS)} jobs.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()