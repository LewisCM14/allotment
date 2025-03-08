import os
import sys

import pytest
from fastapi.testclient import TestClient

from allotment_svc.views import app

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)


@pytest.fixture(name="client")
def _client():
    return TestClient(app)


def test_hello(client):
    """
    Root URL greets the world
    """
    resp = client.get("/")

    assert 200 == resp.status_code
    assert {"message": "Hello World"} == resp.json()
