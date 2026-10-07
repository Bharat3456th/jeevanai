AGENTS = {
    "study": {"name": "Study Agent", "description": "Study plans, summaries and quizzes.",
              "actions": ["create_study_plan", "summarize_notes", "generate_quiz"]},
    "career": {"name": "Career Agent", "description": "Resume score, skill gap and career roadmap.",
               "actions": ["analyze_resume", "skill_gap", "career_roadmap"]},
    "document": {"name": "Document Agent", "description": "Summaries, dates and Q&A on your uploaded documents.",
                 "actions": ["summarize_document", "extract_dates", "ask_document"]},
    "shopping": {"name": "Shopping Agent", "description": "Product tracking and price alerts (never buys anything).",
                 "actions": ["track_product", "check_price", "set_price_alert", "purchase"]},
}

# Default permission per action. Every new user gets these; they can change them later.
DEFAULT_PERMISSIONS = {
    ("study", "create_study_plan"): "ALLOW", ("study", "summarize_notes"): "ALLOW", ("study", "generate_quiz"): "ALLOW",
    ("career", "analyze_resume"): "ALLOW", ("career", "skill_gap"): "ALLOW", ("career", "career_roadmap"): "ALLOW",
    ("document", "summarize_document"): "ASK", ("document", "extract_dates"): "ASK", ("document", "ask_document"): "ASK",
    ("shopping", "track_product"): "ALLOW", ("shopping", "check_price"): "ALLOW",
    ("shopping", "set_price_alert"): "ASK", ("shopping", "purchase"): "BLOCK",
}


def is_valid_action(agent: str, action: str) -> bool:
    return agent in AGENTS and action in AGENTS[agent]["actions"]
