import io
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Document, User

router = APIRouter(prefix="/api/documents", tags=["documents"])
MAX_DOCS = 50


def _extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        try:
            reader = PdfReader(io.BytesIO(data))
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception:
            raise HTTPException(status_code=400, detail="Could not read this PDF (it may be encrypted or damaged)")
    if name.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="ignore")
    raise HTTPException(status_code=415, detail="Only .pdf, .txt and .md files are supported")


@router.post("")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    count = db.scalar(select(func.count()).select_from(Document).where(Document.user_id == user.id)) or 0
    if count >= MAX_DOCS:
        raise HTTPException(status_code=409, detail=f"Document limit reached ({MAX_DOCS}). Delete some first.")
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File too large")
    text = _extract_text(file.filename or "upload", data).replace("\x00", "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="No text found. Scanned/image PDFs need OCR, which is not included.")
    doc = Document(user_id=user.id, filename=(file.filename or "upload")[:255], text=text)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"id": doc.id, "filename": doc.filename, "characters": len(text)}


@router.get("")
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Document).where(Document.user_id == user.id).order_by(Document.id.desc())).all()
    return [{"id": d.id, "filename": d.filename, "characters": len(d.text), "created_at": d.created_at}
            for d in rows]


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    d = db.scalar(select(Document).where(Document.id == doc_id, Document.user_id == user.id))
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(d)
    db.commit()
    return {"deleted": doc_id}
