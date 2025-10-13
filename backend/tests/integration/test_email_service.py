import pytest
from fastapi import HTTPException, status


class TestEmailService:
    @pytest.mark.asyncio
    async def test_test_email_endpoint_with_explicit_email(self, client, mocker):
        mocker.patch(
            "app.api.services.email_service.send_test_email",
            return_value={"message": "sent"},
        )
        response = await client.post("/test-email?email=test@example.com")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Test email sent successfully"

    @pytest.mark.asyncio
    async def test_test_email_endpoint_default_sender(self, client, mocker):
        """Test that email defaults to MAIL_FROM when not provided."""
        mocker.patch(
            "app.api.services.email_service.send_test_email",
            return_value={"message": "sent", "email_id": "test-id"},
        )
        response = await client.post("/test-email")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["message"] == "Test email sent successfully"

    @pytest.mark.asyncio
    async def test_test_email_endpoint_failure(self, client, mocker):
        # Patch the symbol actually imported into main
        mocker.patch(
            "app.main.send_test_email",
            side_effect=HTTPException(status_code=500, detail="smtp down"),
        )
        response = await client.post("/test-email?email=fail@example.com")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        body = response.json()
        assert "detail" in body
        detail = body["detail"]
        # Global exception handler returns list of error objects
        if isinstance(detail, list):
            assert any(d.get("msg") == "smtp down" for d in detail)
        else:
            assert detail == "smtp down"
