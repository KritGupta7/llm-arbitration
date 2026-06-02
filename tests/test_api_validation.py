from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


# ── GET / ─────────────────────────────────────────────────────────────────────

def test_root_returns_200():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


# ── POST /arbitrate/batch — validation ────────────────────────────────────────

def test_batch_empty_list_returns_400():
    response = client.post("/arbitrate/batch", json=[])
    assert response.status_code == 400
    assert "at least one" in response.json()["detail"].lower()


def test_batch_too_many_items_returns_400():
    items = [
        {"question": f"question {i}", "answer": f"answer {i}"}
        for i in range(11)
    ]
    response = client.post("/arbitrate/batch", json=items)
    assert response.status_code == 400
    assert "10" in response.json()["detail"]


def test_batch_exactly_10_items_not_rejected_by_size_check():
    """
    Confirms the size validation passes for 10 items.
    We mock the arbitrate function so no OpenAI call is made.
    """
    from app.models.critique import Critique
    from app.models.arbitration_result import ArbitrationResult

    fake_critique = Critique(
        dimension="accuracy",
        score=4,
        confidence=0.9,
        issues=[],
        explanation="ok",
    )
    fake_result = ArbitrationResult(
        final_score=4.0,
        confidence_level="high",
        summary="looks good",
        confirmed_issues=[],
        accuracy=fake_critique,
        logic=fake_critique,
        completeness=fake_critique,
    )

    items = [
        {"question": f"question {i}", "answer": f"answer {i}"}
        for i in range(10)
    ]

    with patch("app.api.arbitrate", new=AsyncMock(return_value=fake_result)), \
         patch("app.api.save_arbitration") as mock_save:
        from app.models.db_models import ArbitrationRecord
        from datetime import datetime, timezone

        mock_record = ArbitrationRecord()
        mock_record.id = 1
        mock_record.created_at = datetime.now(timezone.utc)
        mock_save.return_value = mock_record

        response = client.post("/arbitrate/batch", json=items)

    # Should not be rejected as 400 due to size
    assert response.status_code != 400 or "10" not in response.json().get("detail", "")


# ── GET /analytics ────────────────────────────────────────────────────────────

def test_analytics_returns_200_with_empty_db():
    with patch("app.services.analytics_service.list_all_arbitrations", return_value=[]):
        response = client.get("/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_arbitrations"] == 0
    assert "average_final_score" in data
    assert "confidence_counts" in data
