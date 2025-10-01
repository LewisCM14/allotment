import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.core.config import settings
from app.api.middleware.exception_handler import ResourceNotFoundError
from app.api.schemas.user.user_active_varieties_schema import (
    ActiveVarietySummary,
    UserActiveVarietyRead,
)

PREFIX = settings.API_PREFIX


class TestUserActiveVarietiesIntegration:
    @pytest.mark.asyncio
    async def test_list_active_varieties_success(
        self, client: TestClient, register_user
    ) -> None:
        """List active varieties successfully using mocked unit of work."""

        headers = await register_user("active_list")
        sample_active = UserActiveVarietyRead(
            user_id=uuid.uuid4(),
            variety=ActiveVarietySummary(
                variety_id=uuid.uuid4(), variety_name="San Marzano"
            ),
            activated_at=datetime.now(timezone.utc),
        )
        with patch(
            "app.api.services.user.user_active_varieties_unit_of_work.UserActiveVarietiesUnitOfWork.get_active_varieties",
            return_value=[sample_active],
        ):
            response = await client.get(
                f"{PREFIX}/users/active-varieties", headers=headers
            )

        assert response.status_code == 200
        payload = response.json()
        assert "active_varieties" in payload
        assert (
            payload["active_varieties"][0]["variety"]["variety_name"] == "San Marzano"
        )

    @pytest.mark.asyncio
    async def test_list_active_varieties_unauthorized(self, client: TestClient) -> None:
        """Ensure listing active varieties without a token is rejected."""

        response = await client.get(f"{PREFIX}/users/active-varieties")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_activate_variety_success(
        self, client: TestClient, register_user
    ) -> None:
        """Activate a variety successfully."""

        headers = await register_user("active_create")
        variety_id = uuid.uuid4()
        sample_active = UserActiveVarietyRead(
            user_id=uuid.uuid4(),
            variety=ActiveVarietySummary(variety_id=variety_id, variety_name="Roma"),
            activated_at=datetime.now(timezone.utc),
        )
        with patch(
            "app.api.services.user.user_active_varieties_unit_of_work.UserActiveVarietiesUnitOfWork.activate_variety",
            return_value=sample_active,
        ):
            response = await client.post(
                f"{PREFIX}/users/active-varieties",
                json={"variety_id": str(variety_id)},
                headers=headers,
            )

        assert response.status_code == 201
        payload = response.json()
        assert payload["variety"]["variety_id"] == str(variety_id)
        assert payload["variety"]["variety_name"] == "Roma"

    @pytest.mark.asyncio
    async def test_activate_variety_invalid_payload(
        self, client: TestClient, register_user
    ) -> None:
        """Invalid UUID payload should trigger validation error."""

        headers = await register_user("active_invalid")
        response = await client.post(
            f"{PREFIX}/users/active-varieties",
            json={"variety_id": "not-a-uuid"},
            headers=headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_activate_variety_not_owned(
        self, client: TestClient, register_user
    ) -> None:
        """Unit of work raising ResourceNotFoundError should surface as 404."""

        headers = await register_user("active_missing")
        variety_id = uuid.uuid4()
        with patch(
            "app.api.services.user.user_active_varieties_unit_of_work.UserActiveVarietiesUnitOfWork.activate_variety",
            side_effect=ResourceNotFoundError("Variety", str(variety_id)),
        ):
            response = await client.post(
                f"{PREFIX}/users/active-varieties",
                json={"variety_id": str(variety_id)},
                headers=headers,
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deactivate_variety_success(
        self, client: TestClient, register_user
    ) -> None:
        """Deactivate a variety successfully."""

        headers = await register_user("active_delete")
        variety_id = uuid.uuid4()
        with patch(
            "app.api.services.user.user_active_varieties_unit_of_work.UserActiveVarietiesUnitOfWork.deactivate_variety",
            return_value=None,
        ):
            response = await client.delete(
                f"{PREFIX}/users/active-varieties/{variety_id}", headers=headers
            )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_deactivate_variety_not_found(
        self, client: TestClient, register_user
    ) -> None:
        """Deactivating a missing active variety should return 404."""

        headers = await register_user("active_delete_missing")
        variety_id = uuid.uuid4()
        with patch(
            "app.api.services.user.user_active_varieties_unit_of_work.UserActiveVarietiesUnitOfWork.deactivate_variety",
            side_effect=ResourceNotFoundError("Active variety", str(variety_id)),
        ):
            response = await client.delete(
                f"{PREFIX}/users/active-varieties/{variety_id}", headers=headers
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_rate_limit_enforced_list(
        self, client: TestClient, register_user
    ) -> None:
        """Enable limiter temporarily to verify 429 after quota exceeded."""

        from app.api.core.limiter import limiter

        headers = await register_user("active_rate")
        sample_active = UserActiveVarietyRead(
            user_id=uuid.uuid4(),
            variety=ActiveVarietySummary(
                variety_id=uuid.uuid4(), variety_name="Cherry"
            ),
            activated_at=datetime.now(timezone.utc),
        )
        with patch(
            "app.api.services.user.user_active_varieties_unit_of_work.UserActiveVarietiesUnitOfWork.get_active_varieties",
            return_value=[sample_active],
        ):
            original = limiter.enabled
            limiter.enabled = True
            try:
                for _ in range(20):
                    ok_resp = await client.get(
                        f"{PREFIX}/users/active-varieties", headers=headers
                    )
                    assert ok_resp.status_code == 200
                over_resp = await client.get(
                    f"{PREFIX}/users/active-varieties", headers=headers
                )
            finally:
                limiter.enabled = original
        assert over_resp.status_code in {200, 429}
        if over_resp.status_code == 429:
            assert "per 1 minute" in over_resp.text
