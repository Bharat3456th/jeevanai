# JeevanAI v1.0

Multi-agent assistant with login, a permission engine (ALLOW / ASK / BLOCK), real offline agents
(optional Claude LLM), document Q&A, price alerts and a built-in web interface.

## Run (Windows)
1. Extract the zip. Open the folder in VS Code.
2. Double-click `start.bat` (or run it in the VS Code terminal).
3. Open http://127.0.0.1:8000/ and create an account.

Manual commands:
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```
Tests: `pytest`   |   API docs: http://127.0.0.1:8000/docs (click Authorize, paste the token)

## What is inside
- Login/registration (JWT), every user has separate documents, products, approvals and permissions
- Study: study plan, summary, multiple-choice quiz
- Career: ATS-style resume score, skill gap per role, month-by-month roadmap
- Document: upload PDF/TXT/MD, summary, date extraction (sorted, ISO format), Q&A (BM25 search)
- Shopping: track product, check price, price alerts with background re-checking; `purchase` never buys
- Approvals, activity log, dashboard, notifications, rate limiting, SSRF protection
- Set `ANTHROPIC_API_KEY` in `.env` for LLM answers; without it agents run offline (rule-based)

## Upgrading from v0.x
The old database has no users. On first start it is renamed to `jeevanai.db.old-backup` and a fresh one is created.

## Not included (needs outside services)
OCR for scanned PDFs, embeddings/vector search, real purchasing/payments, e-mail/SMS alerts,
JavaScript-rendered shop pages (e.g. Amazon/Flipkart usually need a headless browser or official API).
