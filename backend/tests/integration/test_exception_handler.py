import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pytest import fixture

from app.api.middleware.exception_handler import (
    BusinessLogicError,
    ExceptionHandlingMiddleware,
    register_exception_handlers,
)

app = FastAPI()
app.add_middleware(ExceptionHandlingMiddleware)
register_exception_handlers(app)


@app.get("/fail/business")
async def fail_business():
    raise BusinessLogicError(message="Business rule violated")


@app.get("/fail/http")
async def fail_http():
    raise HTTPException(status_code=404, detail="Item not found")


@app.get("/fail/unexpected")
async def fail_unexpected():
    raise Exception("Unexpected failure")


@pytest.fixture(name="client")
def client_fixture():
    """Create a test client with the app configured."""
    return TestClient(app)


class TestIntegrationExceptions:
    @fixture(autouse=True)
    def client(self, client):
        self.client = client

    def test_business_logic_error(self):
        response = self.client.get("/fail/business")
        data = response.json()
        assert response.status_code == 400
        assert data["detail"][0]["msg"] == "Business rule violated"

    def test_http_exception(self):
        response = self.client.get("/fail/http")
        data = response.json()
        assert response.status_code == 404
        assert data["detail"][0]["msg"] == "Item not found"
