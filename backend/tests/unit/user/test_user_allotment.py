from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status

from app.api.v1 import user_allotment


class DummyUser:
    user_id = "dummy-user-id"


class DummyAllotment:
    pass


@pytest.mark.asyncio
async def test_get_user_allotment_not_found(mocker):
    mock_db = MagicMock()
    mock_current_user = DummyUser()
    mock_request = MagicMock()
    # Patch UserUnitOfWork to be a proper async context manager
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)
    mock_uow.get_user_allotment = AsyncMock(return_value=None)
    mocker.patch("app.api.v1.user_allotment.UserUnitOfWork", return_value=mock_uow)
    with pytest.raises(HTTPException) as exc:
        await user_allotment.get_user_allotment(
            mock_request, mock_db, mock_current_user
        )
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_update_user_allotment_success(mocker):
    mock_db = MagicMock()
    mock_current_user = DummyUser()
    mock_request = MagicMock()
    mock_allotment = DummyAllotment()
    # Patch UserUnitOfWork to be a proper async context manager
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)
    mock_uow.update_user_allotment = AsyncMock(
        return_value={
            "user_allotment_id": "id",
            "user_id": "dummy-user-id",
            "allotment_postal_zip_code": "12345",
            "allotment_width_meters": 10.0,
            "allotment_length_meters": 20.0,
        }
    )
    mocker.patch("app.api.v1.user_allotment.UserUnitOfWork", return_value=mock_uow)
    mock_schema = MagicMock()
    mock_schema.model_validate = MagicMock(return_value="validated")
    mocker.patch("app.api.v1.user_allotment.UserAllotmentRead", mock_schema)
    result = await user_allotment.update_user_allotment(
        mock_request, mock_allotment, mock_db, mock_current_user
    )
    assert result == "validated"
