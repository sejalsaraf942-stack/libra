import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.models.user import User
from app.core.security import create_access_token


# In-memory SQLite database for isolated testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app, raise_server_exceptions=False)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(db_session):
    user = db_session.query(User).filter(User.phone == "+919876543210").first()
    if not user:
        user = User(phone="+919876543210", mode="normal")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    token = create_access_token(user.id)
    return {
        "Authorization": f"Bearer {token}",
        "Origin": "http://localhost:3000",
        "Content-Type": "application/json",
    }


def test_original_question_needs_state(client, auth_headers):
    """1. Original question without location should prompt for state clarification."""
    payload = {
        "text": "My landlord is refusing to return my security deposit. What can I do under Indian law?",
        "mode": "normal",
        "history": [],
    }
    res = client.post("/query", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "clarification" in data
    assert "Which state or union territory does this rental dispute arise in?" in data["clarification"]


def test_location_follow_up_with_detailed_prompt(client, auth_headers):
    """2. User replies with state/city and detailed prompt; should receive sources and retained location."""
    q1 = "My landlord is refusing to return my security deposit. What can I do under Indian law?"
    a1 = "Which state or union territory does this rental dispute arise in? State rent laws vary."
    q2 = (
        "I live in Kolkata, West Bengal. I was renting a residential property, and my landlord is refusing "
        "to return my security deposit after I moved out. I want to understand my legal rights, which laws "
        "apply in West Bengal, what steps I can take to recover the deposit, and whether I can send a legal "
        "notice or approach a court or other authority."
    )
    payload = {
        "text": q2,
        "mode": "normal",
        "history": [q1, a1],
    }
    res = client.post("/query", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "clarification" not in data
    assert "short_answer" in data
    assert len(data.get("sources", [])) > 0
    assert data.get("location") is not None
    assert "West Bengal" in data["location"]


def test_location_short_reply(client, auth_headers):
    """User replies simply with 'Kolkata, West Bengal'; should be recognized as location."""
    q1 = "My landlord is refusing to return my security deposit. What can I do under Indian law?"
    a1 = "Which state or union territory does this rental dispute arise in? State rent laws vary."
    payload = {
        "text": "Kolkata, West Bengal",
        "mode": "normal",
        "history": [q1, a1],
    }
    res = client.post("/query", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "clarification" not in data
    assert "short_answer" in data
    assert data.get("location") is not None
    assert "West Bengal" in data["location"]


def test_detailed_tenancy_follow_up_retains_location(client, auth_headers):
    """3. Follow-up question without repeating the state should retain location and not ask again."""
    history = [
        "My landlord is refusing to return my security deposit. What can I do under Indian law?",
        "Which state or union territory does this rental dispute arise in? State rent laws vary.",
        "I live in Kolkata, West Bengal. I was renting a residential property, and my landlord is refusing to return my security deposit.",
        "Based on retrieved sources (DEMO corpus).",
    ]
    follow_up = "What steps can I take to recover the deposit, and whether I can send a legal notice or approach a court or other authority?"
    payload = {
        "text": follow_up,
        "mode": "normal",
        "history": history,
        "location": "West Bengal",
    }
    res = client.post("/query", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    # Should NOT ask for state clarification again!
    assert "clarification" not in data
    assert "short_answer" in data
    assert len(data.get("sources", [])) > 0
    assert data.get("location") is not None
    assert "West Bengal" in data["location"]


def test_backend_error_returns_cors_and_json(client, auth_headers):
    """4. Unhandled server error must return HTTP 500 JSON with CORS headers."""
    # Temporarily register a route that throws an exception
    @app.get("/test-unhandled-error")
    def faulty_endpoint():
        raise RuntimeError("Simulated unexpected backend failure")

    res = client.get("/test-unhandled-error", headers={"Origin": "http://localhost:3000"})
    assert res.status_code == 500
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert res.headers.get("access-control-allow-credentials") == "true"
    data = res.json()
    assert "detail" in data


def test_multi_message_conversation_flow(client, auth_headers):
    """Multi-turn conversation flow across 3 consecutive messages."""
    # Turn 1
    r1 = client.post(
        "/query",
        json={"text": "My landlord is refusing to return my deposit.", "mode": "normal", "history": []},
        headers=auth_headers,
    )
    assert r1.status_code == 200
    d1 = r1.json()
    assert "clarification" in d1

    # Turn 2: Provide location
    history = [
        "My landlord is refusing to return my deposit.",
        d1["clarification"],
    ]
    r2 = client.post(
        "/query",
        json={"text": "I live in Kolkata, West Bengal", "mode": "normal", "history": history},
        headers=auth_headers,
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert "short_answer" in d2
    assert d2.get("location") is not None

    # Turn 3: Follow-up question
    history.extend([
        "I live in Kolkata, West Bengal",
        d2["short_answer"],
    ])
    r3 = client.post(
        "/query",
        json={
            "text": "Can I approach a consumer forum or rent tribunal?",
            "mode": "normal",
            "history": history,
            "location": d2.get("location"),
        },
        headers=auth_headers,
    )
    assert r3.status_code == 200
    d3 = r3.json()
    assert "clarification" not in d3
    assert "short_answer" in d3
    assert len(d3.get("sources", [])) > 0
