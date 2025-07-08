from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.middleware.exceptions import (
    BusinessLogicError,
    ExceptionHandlingMiddleware,
    register_exception_handlers,
)

app = FastAPI()
register_exception_handlers(app)
app.add_middleware(ExceptionHandlingMiddleware)


@app.get("/fail/business")
async def fail_business():
    raise BusinessLogicError(message="Business rule violated")


@app.get("/fail/http")
async def fail_http():
    raise HTTPException(status_code=404, detail="Item not found")


@app.get("/fail/unexpected")
async def fail_unexpected():
    raise Exception("Unexpected failure")


# Create client without re‑raising server exceptions
client = TestClient(app, raise_server_exceptions=False)


class TestIntegrationExceptions:
    def test_business_logic_error(self):
        response = client.get("/fail/business")
        data = response.json()
        assert response.status_code == 400
        assert data["detail"][0]["msg"] == "Business rule violated"

    def test_http_exception(self):
        response = client.get("/fail/http")
        data = response.json()
        assert response.status_code == 404
        assert data["detail"][0]["msg"] == "Item not found"

    def test_general_exception(self):
        response = client.get("/fail/unexpected")
        data = response.json()
        assert response.status_code == 500
        assert data["detail"][0]["msg"] == "An unexpected error occurred"
        data = response.json()
        assert response.status_code == 500
        assert data["detail"][0]["msg"] == "An unexpected error occurred"
