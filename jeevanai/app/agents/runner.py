from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from app.agents import study, career, document, shopping


@dataclass
class Context:
    db: Session
    user_id: int
    message: str = ""
    payload: dict = field(default_factory=dict)


HANDLERS = {
    ("study", "create_study_plan"): study.create_study_plan,
    ("study", "summarize_notes"): study.summarize_notes,
    ("study", "generate_quiz"): study.generate_quiz,
    ("career", "analyze_resume"): career.analyze_resume,
    ("career", "skill_gap"): career.skill_gap,
    ("career", "career_roadmap"): career.career_roadmap,
    ("document", "summarize_document"): document.summarize_document,
    ("document", "extract_dates"): document.extract_dates,
    ("document", "ask_document"): document.ask_document,
    ("shopping", "track_product"): shopping.track_product,
    ("shopping", "check_price"): shopping.check_price,
    ("shopping", "set_price_alert"): shopping.set_price_alert,
    ("shopping", "purchase"): shopping.purchase,
}


def run_agent(agent: str, action: str, message: str, payload: dict, db: Session, user_id: int) -> dict:
    handler = HANDLERS.get((agent, action))
    if not handler:
        raise ValueError(f"No handler for {agent}/{action}")
    result = handler(Context(db=db, user_id=user_id, message=message, payload=payload or {}))
    return {"agent": agent, "action": action, **result}
