"""
Email Service Tests
"""

from fastapi import status

from app.api.core.config import settings
from tests.integration.test_user import mock_email_service

PREFIX = settings.API_PREFIX


class TestEmailService:
    def test_test_email_endpoint(self, client, mocker):
        """Test the email configuration test endpoint."""
        mock_send_test = mock_email_service(mocker, "app.main.send_test_email")

        test_email = "test@example.com"
        response = client.post(f"/test-email?email={test_email}")

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()

        mock_send_test.assert_called_once()
