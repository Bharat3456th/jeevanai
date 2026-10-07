import json
import random
import re
from app.core.llm import complete
from app.agents.textutils import sentences, extractive_summary, words

SYS = "You are a precise study assistant. Be concise, structured and accurate."


def _num(v, default, lo, hi):
    try:
        return max(lo, min(float(v), hi))
    except (TypeError, ValueError):
        return default


def create_study_plan(ctx):
    topic = (ctx.payload.get("topic") or ctx.message or "").strip()
    if not topic:
        raise ValueError("Give a topic.")
    days = int(_num(ctx.payload.get("days"), 7, 1, 60))
    hours = _num(ctx.payload.get("hours_per_day"), 2, 0.5, 16)
    text = complete(SYS, f"Create a {days}-day study plan for '{topic}' at {hours} hours/day. "
                         f"Give each day a goal, 2-4 tasks and a short self-test. Plain text.")
    if text:
        return {"response": text, "data": {"topic": topic, "days": days}, "mode": "llm"}
    phases = ["Foundations and key terms", "Core concepts", "Worked examples", "Practice problems",
              "Weak-spot review", "Mock test", "Final revision"]
    plan = []
    for d in range(1, days + 1):
        ph = phases[min(int((d - 1) / days * len(phases)), len(phases) - 1)]
        plan.append({"day": d, "goal": f"{ph} - {topic}", "hours": hours,
                     "tasks": ["Study / read the material", "Write short notes", "Self-test 5 questions"]})
    return {"response": f"{days}-day plan for {topic} created (offline template).",
            "data": {"plan": plan}, "mode": "offline"}


def summarize_notes(ctx):
    notes = (ctx.payload.get("notes") or ctx.message or "").strip()
    if len(notes) < 40:
        raise ValueError("Send the notes to summarize (at least a few sentences).")
    text = complete(SYS, f"Summarize these notes as short bullet points, then list 3 key terms:\n\n{notes[:12000]}")
    if text:
        return {"response": text, "data": {}, "mode": "llm"}
    return {"response": extractive_summary(notes), "data": {}, "mode": "offline"}


def offline_quiz(source: str, n: int):
    rnd = random.Random(42)
    pool = sorted({w for w in words(source) if len(w) > 4})
    quiz = []
    for s in sentences(source):
        cands = sorted({c for c in words(s) if len(c) > 3}, key=len, reverse=True)
        if not cands:
            continue
        ans = cands[0]
        item = {"question": re.sub(re.escape(ans), "_____", s, count=1, flags=re.I), "answer": ans}
        distract = [w for w in pool if w != ans]
        rnd.shuffle(distract)
        opts = [ans] + distract[:3]
        if len(opts) >= 3:
            rnd.shuffle(opts)
            item["options"] = opts
        quiz.append(item)
        if len(quiz) >= n:
            break
    return quiz


def generate_quiz(ctx):
    source = (ctx.payload.get("notes") or ctx.message or "").strip()
    n = int(_num(ctx.payload.get("count"), 5, 1, 15))
    if len(source) < 40:
        raise ValueError("Send notes with some content to build a quiz from.")
    text = complete(SYS, "Return ONLY a JSON array of %d objects with keys question, options (4 strings), answer "
                         "(one of the options), explanation. Source:\n\n%s" % (n, source[:10000]), max_tokens=2500)
    if text:
        try:
            cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
            quiz = json.loads(cleaned)
            if isinstance(quiz, list) and quiz:
                return {"response": f"Generated {len(quiz)} questions.", "data": {"quiz": quiz}, "mode": "llm"}
        except ValueError:
            pass
    quiz = offline_quiz(source, n)
    return {"response": f"Generated {len(quiz)} multiple-choice questions (offline).",
            "data": {"quiz": quiz}, "mode": "offline"}
