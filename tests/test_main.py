
import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Give each test its own temporary database.
    test_db = tmp_path / "test_agentops.db"
    monkeypatch.setattr(database, "DATABASE_PATH", test_db)

    database.init_db()

    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["storage"] == "sqlite"


def test_create_and_list_event(client):
    payload = {
        "trace_id": "trace-test-001",
        "event_type": "tool_call",
        "name": "search_documents",
        "status": "success",
        "duration_ms": 120,
    }

    create_response = client.post("/events", json=payload)

    assert create_response.status_code == 201

    saved_event = create_response.json()
    assert saved_event["trace_id"] == "trace-test-001"
    assert saved_event["event_id"]

    list_response = client.get(
        "/events",
        params={"trace_id": "trace-test-001"},
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_reject_negative_duration(client):
    payload = {
        "trace_id": "trace-test-002",
        "event_type": "tool_call",
        "name": "search_documents",
        "status": "success",
        "duration_ms": -1,
    }

    response = client.post("/events", json=payload)

    assert response.status_code == 422


def test_missing_event_returns_404(client):
    response = client.get("/events/nonexistent-id")

    assert response.status_code == 404


def test_analytics_counts_events(client):
    client.post(
        "/events",
        json={
            "trace_id": "analytics-test",
            "event_type": "tool_call",
            "name": "search_documents",
            "status": "success",
            "duration_ms": 120,
        },
    )

    client.post(
        "/events",
        json={
            "trace_id": "analytics-test",
            "event_type": "llm_call",
            "name": "generate_answer",
            "status": "error",
            "duration_ms": 300,
        },
    )

    response = client.get(
        "/analytics",
        params={"trace_id": "analytics-test"},
    )

    assert response.status_code == 200

    result = response.json()
    assert result["total_events"] == 2
    assert result["failed_events"] == 1
    assert result["success_events"] == 1
    assert result["average_duration_ms"] == 210.0



def test_trace_summary(client):
    client.post(
        "/events",
        json={
            "trace_id": "summary-test",
            "event_type": "agent_start",
            "name": "document_assistant",
            "status": "success",
        },
    )

    client.post(
        "/events",
        json={
            "trace_id": "summary-test",
            "event_type": "tool_call",
            "name": "search_documents",
            "status": "success",
            "duration_ms": 120,
        },
    )

    client.post(
        "/events",
        json={
            "trace_id": "summary-test",
            "event_type": "agent_end",
            "name": "document_assistant",
            "status": "success",
        },
    )

    response = client.get("/traces/summary-test")

    assert response.status_code == 200

    result = response.json()
    assert result["trace_id"] == "summary-test"
    assert result["status"] == "success"
    assert result["event_count"] == 3
    assert result["failed_event_count"] == 0
    assert result["total_event_duration_ms"] == 120
    assert result["trace_duration_ms"] is not None
    assert result["trace_duration_ms"] >= 0
    assert len(result["events"]) == 3



def test_missing_trace_returns_404(client):
    response = client.get("/traces/trace-that-does-not-exist")

    assert response.status_code == 404


def test_trace_summary_reports_failed_trace(client):
    client.post(
        "/events",
        json={
            "trace_id": "failed-trace-test",
            "event_type": "agent_start",
            "name": "document_assistant",
            "status": "success",
        },
    )

    client.post(
        "/events",
        json={
            "trace_id": "failed-trace-test",
            "event_type": "error",
            "name": "search_documents",
            "status": "error",
            "duration_ms": 250,
        },
    )

    response = client.get("/traces/failed-trace-test")

    assert response.status_code == 200

    result = response.json()
    assert result["status"] == "error"
    assert result["event_count"] == 2
    assert result["failed_event_count"] == 1
