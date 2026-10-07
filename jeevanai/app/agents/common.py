from app.db.models import Document


def num(payload: dict, key: str, default, lo, hi, cast=int):
    v = payload.get(key, default)
    if v in (None, ""):
        v = default
    try:
        v = cast(v)
    except (TypeError, ValueError):
        raise ValueError(f"'{key}' must be a number.")
    return max(lo, min(v, hi))


def load_document(ctx, doc_id=None) -> Document:
    doc_id = doc_id or ctx.payload.get("document_id")
    if not doc_id:
        raise ValueError("Select a document first (upload one in the Documents tab).")
    try:
        doc_id = int(doc_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid document id.")
    doc = ctx.db.query(Document).filter_by(id=doc_id, user_id=ctx.user_id).first()
    if not doc:
        raise ValueError("Document not found.")
    return doc


def source_text(ctx, key: str) -> str:
    """Text from payload[key], else the message, else the selected document."""
    t = str(ctx.payload.get(key) or ctx.message or "").strip()
    if not t and ctx.payload.get("document_id"):
        t = load_document(ctx).text.strip()
    return t
