from sqlalchemy import select
from app.core.llm import complete
from app.db.models import Document
from app.agents.textutils import extractive_summary, top_chunks
from app.agents.dates import find_dates

SYS = "You answer strictly from the provided document. If the answer is not there, say so."


def _doc(ctx) -> Document:
    doc_id = ctx.payload.get("document_id")
    try:
        doc_id = int(doc_id)
    except (TypeError, ValueError):
        raise ValueError("Choose a document first (upload one in the Documents tab).")
    doc = ctx.db.scalar(select(Document).where(Document.id == doc_id, Document.user_id == ctx.user_id))
    if not doc:
        raise ValueError("Document not found.")
    return doc


def summarize_document(ctx):
    doc = _doc(ctx)
    text = complete(SYS, f"Summarize this document in 6 bullets:\n\n{doc.text[:15000]}")
    if text:
        return {"response": text, "data": {"document": doc.filename}, "mode": "llm"}
    return {"response": extractive_summary(doc.text), "data": {"document": doc.filename}, "mode": "offline"}


def extract_dates(ctx):
    doc = _doc(ctx)
    dates = find_dates(doc.text)
    return {"response": f"Found {len(dates)} date(s) in {doc.filename}.", "data": {"dates": dates}, "mode": "offline"}


def ask_document(ctx):
    doc = _doc(ctx)
    question = (ctx.message or "").strip()
    if not question:
        raise ValueError("Type your question.")
    chunks = top_chunks(doc.text, question)
    if not chunks:
        return {"response": "No relevant passage found in this document.", "data": {"sources": []}, "mode": "offline"}
    text = complete(SYS, "Document excerpts:\n" + "\n---\n".join(chunks) + f"\n\nQuestion: {question}")
    if text:
        return {"response": text, "data": {"sources": chunks}, "mode": "llm"}
    return {"response": chunks[0], "data": {"sources": chunks}, "mode": "offline"}
