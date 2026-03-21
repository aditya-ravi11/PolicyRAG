import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    # Patch dependencies before importing app
    with patch("policyrag.api.deps._cache") as mock_cache, \
         patch("policyrag.ingestion.embedder._get_model"):
        mock_cache.connect = AsyncMock()
        mock_cache.close = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        from policyrag.main import app
        with TestClient(app) as c:
            yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_documents(client):
    with patch("policyrag.api.routes.documents.DocumentRepository") as MockRepo:
        repo = MockRepo.return_value
        repo.list_all = AsyncMock(return_value=[])
        resp = client.get("/api/v1/documents")
        assert resp.status_code == 200
        assert resp.json() == []


def test_get_models_active(client):
    resp = client.get("/api/v1/models/active")
    assert resp.status_code == 200
    data = resp.json()
    assert "provider" in data
    assert "model" in data


def test_switch_model(client):
    resp = client.post("/api/v1/models/switch?provider=ollama&model=llama3.1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "ollama"
    assert data["model"] == "llama3.1"


def test_upload_non_pdf_rejected(client):
    resp = client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", b"content", "text/plain")},
    )
    assert resp.status_code == 400


def test_evaluation_analytics(client):
    with patch("policyrag.api.routes.evaluation.EvaluationRepository") as MockRepo:
        repo = MockRepo.return_value
        repo.get_analytics = AsyncMock(return_value={
            "total_queries": 0,
            "avg_faithfulness": 0.0,
            "avg_hallucination": 0.0,
            "avg_citation_precision": 0.0,
            "avg_citation_recall": 0.0,
            "avg_context_relevance": 0.0,
            "avg_trust_score": 0.0,
            "avg_completeness": 0.0,
        })
        resp = client.get("/api/v1/evaluation/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_queries" in data
        assert "avg_trust_score" in data
