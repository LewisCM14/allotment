import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.middleware.exception_handler import (
    BusinessLogicError,
    ExceptionHandlingMiddleware,
    general_exception_handler,
    register_exception_handlers,
)

app = FastAPI()
app.add_middleware(ExceptionHandlingMiddleware)
register_exception_handlers(app)
app.add_exception_handler(Exception, general_exception_handler)


@app.get("/fail/business")
async def fail_business():
    raise BusinessLogicError(message="Business rule violated")


@app.get("/fail/http")
async def fail_http():
    raise HTTPException(status_code=404, detail="Item not found")


@app.get("/fail/unexpected")
async def fail_unexpected():
    raise Exception("Unexpected failure")


@pytest.fixture()
def client():
    # Disable re-raising server exceptions so we can assert on standardized error responses
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    "path,expected_status,expected_msg_contains",
    [
        ("/fail/business", 400, "Business rule violated"),
        ("/fail/http", 404, "Item not found"),
        ("/fail/unexpected", 500, "An unexpected error occurred"),
    ],
)
def test_exceptions(client, path, expected_status, expected_msg_contains):
    response = client.get(path)
    data = response.json()
    assert response.status_code == expected_status
    assert expected_msg_contains.lower() in data["detail"][0]["msg"].lower()
