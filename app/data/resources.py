# Curated learning links, mostly official documentation. This is NOT live course data.
# Open each link once to confirm it still works; sites sometimes move pages.
RESOURCES = {
    "Python": [("Official Python Tutorial", "https://docs.python.org/3/tutorial/", "Documentation")],
    "SQL": [("SQL Tutorial (W3Schools)", "https://www.w3schools.com/sql/", "Tutorial")],
    "MySQL": [("MySQL Tutorial (official)", "https://dev.mysql.com/doc/refman/8.0/en/tutorial.html", "Documentation")],
    "JavaScript": [("MDN JavaScript Guide", "https://developer.mozilla.org/en-US/docs/Web/JavaScript", "Documentation")],
    "HTML": [("MDN Learn HTML", "https://developer.mozilla.org/en-US/docs/Learn/HTML", "Tutorial")],
    "CSS": [("MDN Learn CSS", "https://developer.mozilla.org/en-US/docs/Learn/CSS", "Tutorial")],
    "FastAPI": [("FastAPI Tutorial (official)", "https://fastapi.tiangolo.com/tutorial/", "Documentation")],
    "Django": [("Django Tutorial (official)", "https://docs.djangoproject.com/en/stable/intro/tutorial01/", "Documentation")],
    "Flask": [("Flask Quickstart (official)", "https://flask.palletsprojects.com/en/stable/quickstart/", "Documentation")],
    "React": [("React: Learn", "https://react.dev/learn", "Documentation")],
    "Node.js": [("Node.js Learn", "https://nodejs.org/en/learn", "Documentation")],
    "Java": [("Dev.java Learn", "https://dev.java/learn/", "Tutorial")],
    "Spring Boot": [("Spring Boot Guide", "https://spring.io/guides/gs/spring-boot", "Tutorial")],
    "Git": [("Pro Git Book (free)", "https://git-scm.com/book/en/v2", "Book")],
    "Docker": [("Docker Get Started", "https://docs.docker.com/get-started/", "Documentation")],
    "AWS": [("AWS Getting Started", "https://aws.amazon.com/getting-started/", "Documentation")],
    "Linux": [("Linux Journey", "https://linuxjourney.com/", "Tutorial")],
    "REST APIs": [("Web API Design Best Practices", "https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design", "Documentation")],
    "Pandas": [("10 Minutes to pandas", "https://pandas.pydata.org/docs/user_guide/10min.html", "Documentation")],
    "NumPy": [("NumPy Absolute Beginners", "https://numpy.org/doc/stable/user/absolute_beginners.html", "Documentation")],
    "Machine Learning": [("scikit-learn Getting Started", "https://scikit-learn.org/stable/getting_started.html", "Documentation")],
    "Data Analysis": [("pandas Getting Started", "https://pandas.pydata.org/docs/getting_started/index.html", "Documentation")],
    "Power BI": [("Power BI Documentation", "https://learn.microsoft.com/en-us/power-bi/", "Documentation")],
    "Tableau": [("Tableau Training", "https://www.tableau.com/learn/training", "Tutorial")],
    "Statistics": [("Khan Academy Statistics", "https://www.khanacademy.org/math/statistics-probability", "Course")],
    "Testing": [("pytest Getting Started", "https://docs.pytest.org/en/stable/getting-started.html", "Documentation")],
    "Kubernetes": [("Kubernetes Basics", "https://kubernetes.io/docs/tutorials/kubernetes-basics/", "Tutorial")],
    "Figma": [("Figma Help Center", "https://help.figma.com/", "Documentation")],
}


def resources_for(skill: str) -> list[dict]:
    return [{"title": t, "url": u, "kind": k} for t, u, k in RESOURCES.get(skill, [])]