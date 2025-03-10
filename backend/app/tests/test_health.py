"""
Health API Tests
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

API_VERSION = "api/v1"


@pytest.fixture(name="client")
def _client():
    return TestClient(app)


def test_hello(client):
    """
    Root URL greets the world
    """
    resp = client.get("/")

    assert 200 == resp.status_code
    assert {"message": "Welcome to the Allotment Service API!"} == resp.json()


def test_health(client):
    """
    Health Endpoint returns OK
    """
    resp = client.get(f"{API_VERSION}/health")

    assert 200 == resp.status_code
    assert {"status": "OK"} == resp.json()
