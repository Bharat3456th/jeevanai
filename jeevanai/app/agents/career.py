import re
from app.core.llm import complete

SYS = "You are a practical career coach. Be specific and honest."

SKILLS = ["python", "java", "javascript", "typescript", "c++", "sql", "react", "node", "fastapi", "django", "flask",
          "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux", "machine learning", "deep learning",
          "pandas", "numpy", "tensorflow", "pytorch", "nlp", "rest api", "html", "css", "mongodb", "postgresql",
          "redis", "ci/cd", "data analysis", "excel", "power bi", "tableau", "communication", "leadership",
          "kotlin", "android", "firebase", "networking", "wireshark", "penetration testing", "cryptography",
          "spring boot", "security"]
ALIASES = {"js": "javascript", "ts": "typescript", "k8s": "kubernetes", "postgres": "postgresql",
           "nodejs": "node", "node.js": "node", "reactjs": "react", "ml": "machine learning",
           "dl": "deep learning", "sklearn": "machine learning", "scikit-learn": "machine learning"}

ROLE_SKILLS = {
    "backend developer": ["python", "sql", "rest api", "fastapi", "docker", "git", "postgresql", "redis", "linux"],
    "frontend developer": ["javascript", "typescript", "react", "html", "css", "git", "rest api"],
    "full stack developer": ["javascript", "react", "node", "sql", "rest api", "docker", "git", "html", "css"],
    "data analyst": ["sql", "excel", "python", "pandas", "data analysis", "power bi", "tableau"],
    "data scientist": ["python", "pandas", "numpy", "machine learning", "sql", "deep learning", "data analysis"],
    "ml engineer": ["python", "machine learning", "deep learning", "pytorch", "tensorflow", "docker", "aws", "git"],
    "devops engineer": ["linux", "docker", "kubernetes", "aws", "ci/cd", "git", "python"],
    "android developer": ["kotlin", "java", "android", "firebase", "rest api", "git", "sql"],
    "cybersecurity analyst": ["networking", "linux", "security", "wireshark", "penetration testing", "cryptography", "python"],
}
ROLE_PROJECTS = {
    "backend developer": ["REST API with login", "Task manager on PostgreSQL", "Dockerised microservice"],
    "frontend developer": ["Responsive portfolio", "React dashboard", "Weather app with API"],
    "full stack developer": ["Blog with login", "E-commerce cart", "Chat app"],
    "data analyst": ["Sales dashboard", "SQL case study", "Excel to Power BI report"],
    "data scientist": ["House price prediction", "Customer churn model", "Sentiment analysis"],
    "ml engineer": ["Model served via API", "Image classifier", "End-to-end ML pipeline"],
    "devops engineer": ["CI/CD pipeline", "Dockerised app on cloud", "Kubernetes deployment"],
    "android developer": ["To-do app", "Notes app with Firebase", "API-driven news app"],
    "cybersecurity analyst": ["Network scan report", "Password audit tool", "Log analysis project"],
}


def _found(text: str):
    t = text.lower()
    out = set()
    for name in list(SKILLS) + list(ALIASES):
        if re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", t):
            out.add(ALIASES.get(name, name))
    return sorted(out)


def analyze_resume(ctx):
    resume = (ctx.payload.get("resume") or ctx.message or "").strip()
    if len(resume) < 50:
        raise ValueError("Paste resume text (at least a few lines).")
    low = resume.lower()
    skills = _found(resume)
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", resume)
    phone = re.search(r"(?:\+?\d{1,3}[\s-]?)?[6-9]\d{9}\b|\+\d[\d\s-]{8,14}\d", resume)
    links = [k for k in ("linkedin", "github", "portfolio") if k in low]
    sections = [s for s in ("summary", "objective", "education", "experience", "projects", "skills", "certifications")
                if re.search(r"\b" + s, low)]
    years = [int(x) for x in re.findall(r"(\d{1,2})\+?\s*(?:years|yrs)", low)]
    words_n = len(resume.split())
    has_numbers = bool(re.search(r"\d+\s*%|\d+\s*(users|clients|projects|customers|records)", low))

    score = min(len(sections), 5) * 10
    score += 10 if email else 0
    score += 5 if phone else 0
    score += 5 if links else 0
    score += 10 if len(skills) >= 8 else 5 if len(skills) >= 5 else 0
    score += 10 if has_numbers else 0
    score += 10 if 150 <= words_n <= 1000 else 0
    data = {"ats_score": min(score, 100), "skills_found": skills, "sections_found": sections,
            "email": email.group(0) if email else None, "phone": phone.group(0) if phone else None,
            "links": links, "years_experience_mentioned": max(years) if years else None, "word_count": words_n}
    text = complete(SYS, f"Review this resume: strengths, weaknesses, 5 concrete improvements.\n\n{resume[:10000]}")
    if text:
        return {"response": text, "data": data, "mode": "llm"}
    tips = []
    if not email:
        tips.append("Add a contact email.")
    if not phone:
        tips.append("Add a phone number.")
    if not links:
        tips.append("Add LinkedIn/GitHub links.")
    if len(skills) < 5:
        tips.append("List more concrete technical skills.")
    if not has_numbers:
        tips.append("Add measurable results (numbers, percentages).")
    for s in ("education", "experience", "projects", "skills"):
        if s not in sections:
            tips.append(f"Add a '{s.title()}' section.")
    if words_n < 150:
        tips.append("Resume looks too short.")
    return {"response": f"ATS-style score: {data['ats_score']}/100. " + (" ".join(tips) or "Looks solid."),
            "data": data, "mode": "offline"}


def skill_gap(ctx):
    role = (ctx.payload.get("target_role") or "").lower().strip()
    resume = (ctx.payload.get("resume") or ctx.message or "")
    if role not in ROLE_SKILLS:
        raise ValueError(f"target_role must be one of: {', '.join(ROLE_SKILLS)}")
    if len(resume.strip()) < 20:
        raise ValueError("Paste your resume text or skills list.")
    have = set(_found(resume))
    need = ROLE_SKILLS[role]
    missing = [s for s in need if s not in have]
    pct = round(100 * (len(need) - len(missing)) / len(need))
    return {"response": f"Match for {role}: {pct}%. Missing: {', '.join(missing) or 'nothing'}.",
            "data": {"role": role, "match_percent": pct, "have": sorted(have & set(need)), "missing": missing},
            "mode": "offline"}


def career_roadmap(ctx):
    role = (ctx.payload.get("target_role") or ctx.message or "").strip()
    if not role:
        raise ValueError("Give target_role.")
    try:
        months = max(1, min(int(ctx.payload.get("months", 6)), 24))
    except (TypeError, ValueError):
        months = 6
    text = complete(SYS, f"Make a {months}-month roadmap to become a {role}. Per month: skills, one project, one milestone.")
    if text:
        return {"response": text, "data": {}, "mode": "llm"}
    skills = ROLE_SKILLS.get(role.lower(), [])
    projects = ROLE_PROJECTS.get(role.lower(), ["Portfolio project"])
    per = max(1, -(-len(skills) // months)) if skills else 1
    steps = []
    for m in range(months):
        focus = skills[m * per:(m + 1) * per] or ["portfolio polish", "mock interviews", "job applications"]
        steps.append({"month": m + 1, "focus": focus, "project": projects[m % len(projects)]})
    return {"response": f"{months}-month roadmap for {role} (offline template).",
            "data": {"roadmap": steps}, "mode": "offline"}
