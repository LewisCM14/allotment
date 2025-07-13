"""
Email Service Tests
"""

import pytest
from fastapi import status

from app.api.core.config import settings

PREFIX = settings.API_PREFIX


class TestEmailService:
    @pytest.mark.asyncio
    async def test_test_email_endpoint(self, client):
        """Test the email configuration test endpoint."""
        test_email = "test@example.com"
        response = await client.post(f"/test-email?email={test_email}")

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()
        assert response.json()["message"] == "Test email sent successfully"
