import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "gemini_key_configured" in data

def test_list_repositories_endpoint():
    response = client.get("/api/upload")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
