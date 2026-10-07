import os
import tempfile

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["JWT_SECRET"] = "test-secret"
os.environ["PRICE_CHECK_MINUTES"] = "0"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.agents.shopping import is_safe_url, parse_price  # noqa: E402
from app.agents.textutils import top_chunks  # noqa: E402
from app.core.security import hash_password, verify_password  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


PROFILE = {"name": "Tester", "phone": "9876543210", "state": "Delhi", "city": "New Delhi",
           "occupation": "Student", "dob": "2000-01-15"}


def signup(client, email, name="Tester"):
    body = {**PROFILE, "name": name, "email": email, "password": "password123"}
    r = client.post("/api/auth/register", json=body)
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def run(client, h, **body):
    return client.post("/api/agent/run", json=body, headers=h)


def test_status_and_ui(client):
    assert client.get("/api/status").json()["status"] == "running"
    assert "JeevanAI" in client.get("/").text


def test_auth_required(client):
    assert client.get("/api/agents").status_code == 401
    assert run(client, {}, agent="study", action="create_study_plan").status_code == 401


def test_register_login_me(client):
    signup(client, "a@example.com")
    assert client.post("/api/auth/register", json={**PROFILE, "email": "a@example.com", "password": "password123"}).status_code == 409
    assert client.post("/api/auth/register", json={**PROFILE, "email": "bad", "password": "password123"}).status_code == 422
    r = client.post("/api/auth/login", json={"email": "a@example.com", "password": "password123"})
    assert r.status_code == 200
    h = {"Authorization": "Bearer " + r.json()["access_token"]}
    assert client.get("/api/auth/me", headers=h).json()["email"] == "a@example.com"
    assert client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong-pass"}).status_code == 401


def test_study_plan_and_blocked_purchase(client):
    h = signup(client, "b@example.com")
    r = run(client, h, agent="study", action="create_study_plan", payload={"topic": "Python", "days": 3})
    assert r.json()["status"] == "allowed" and len(r.json()["data"]["plan"]) == 3
    assert run(client, h, agent="shopping", action="purchase").json()["status"] == "blocked"
    assert run(client, h, agent="study", action="nope").status_code == 400


def test_document_approval_flow_and_isolation(client):
    h1, h2 = signup(client, "c@example.com"), signup(client, "d@example.com")
    up = client.post("/api/documents", headers=h1,
                     files={"file": ("a.txt", b"The exam is on 15 March 2026. Bring your ID card.", "text/plain")})
    doc_id = up.json()["id"]
    r = run(client, h1, agent="document", action="extract_dates", payload={"document_id": doc_id})
    assert r.json()["status"] == "approval_required"
    aid = r.json()["approval_id"]
    assert client.post(f"/api/approvals/{aid}/approve", headers=h2).status_code == 404  # not their approval
    ok = client.post(f"/api/approvals/{aid}/approve", headers=h1)
    assert ok.status_code == 200 and ok.json()["data"]["dates"][0]["date"].startswith("15 March")
    assert client.post(f"/api/approvals/{aid}/approve", headers=h1).status_code == 409
    # another user cannot read this document, even by id
    run(client, h2, agent="document", action="summarize_document", payload={"document_id": doc_id})
    aid2 = client.get("/api/approvals", headers=h2).json()[0]["id"]
    assert client.post(f"/api/approvals/{aid2}/approve", headers=h2).status_code == 400
    assert client.get("/api/documents", headers=h2).json() == []


def test_permission_update_and_reset(client):
    h = signup(client, "e@example.com")
    assert client.post("/api/permissions", headers=h,
                       json={"agent": "study", "action": "generate_quiz", "permission": "x"}).status_code == 400
    client.post("/api/permissions", headers=h, json={"agent": "study", "action": "generate_quiz", "permission": "BLOCK"})
    assert run(client, h, agent="study", action="generate_quiz", message="x" * 60).json()["status"] == "blocked"
    client.post("/api/permissions/reset", headers=h)
    assert run(client, h, agent="study", action="generate_quiz", message="Python is a language. " * 5
               ).json()["status"] == "allowed"


def test_products_and_notifications(client):
    h = signup(client, "f@example.com")
    assert run(client, h, agent="shopping", action="track_product", payload={"url": "http://127.0.0.1/x"}).status_code == 400
    assert client.get("/api/products", headers=h).json() == []
    assert client.get("/api/notifications", headers=h).json() == {"unread": 0, "items": []}


def test_helpers():
    assert parse_price('<script type="application/ld+json">{"offers":{"price":"1,499.00","priceCurrency":"INR"}}</script>') == (1499.0, "INR")
    assert not is_safe_url("http://127.0.0.1/") and not is_safe_url("ftp://example.com")
    assert verify_password("secret123", hash_password("secret123")) and not verify_password("nope", hash_password("secret123"))
    text = "Cats sleep a lot. " * 30 + "The invoice number is 4471 and is due on Friday. " + "Dogs bark. " * 30
    assert "4471" in top_chunks(text, "what is the invoice number")[0]


def test_registration_details_and_admin(client):
    bad = {**PROFILE, "email": "x@example.com", "password": "password123", "phone": "123"}
    assert client.post("/api/auth/register", json=bad).status_code == 422
    assert client.post("/api/auth/register", json={**bad, "phone": "9876543210", "state": "Nowhere"}).status_code == 422
    assert len(client.get("/api/auth/meta").json()["states"]) == 36
    h = signup(client, "plain@example.com")
    me = client.get("/api/auth/me", headers=h).json()
    assert me["role"] in ("user", "admin") and me["profile_complete"] is True
    if me["role"] == "user":
        assert client.get("/api/admin/stats", headers=h).status_code == 403
    upd = client.put("/api/auth/me", headers=h, json={**PROFILE, "city": "Jaipur", "state": "Rajasthan"})
    assert upd.json()["city"] == "Jaipur"
    assert client.post("/api/auth/change-password", headers=h,
                       json={"old_password": "wrong-old", "new_password": "newpass123"}).status_code == 400
