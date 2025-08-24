from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from app.api.v1 import user_allotment
from tests.test_helpers import build_user_stub, mock_user_uow


class DummyAllotment:  # kept minimal
    ...


@pytest.mark.asyncio
async def test_get_user_allotment_not_found(mocker):
    mock_db = MagicMock()
    mock_current_user = build_user_stub(mocker, user_id="dummy-user-id")
    mock_request = MagicMock()
    mock_user_uow(
        mocker,
        path="app.api.v1.user_allotment.UserUnitOfWork",
        methods={"get_user_allotment": None},
    )
    with pytest.raises(HTTPException) as exc:
        await user_allotment.get_user_allotment(
            mock_request, mock_db, mock_current_user
        )
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_update_user_allotment_success(mocker):
    mock_db = MagicMock()
    mock_current_user = build_user_stub(mocker, user_id="dummy-user-id")
    mock_request = MagicMock()
    mock_allotment = DummyAllotment()
    updated_payload = {
        "user_allotment_id": "id",
        "user_id": "dummy-user-id",
        "allotment_postal_zip_code": "12345",
        "allotment_width_meters": 10.0,
        "allotment_length_meters": 20.0,
    }
    mock_user_uow(
        mocker,
        path="app.api.v1.user_allotment.UserUnitOfWork",
        methods={"update_user_allotment": updated_payload},
    )
    mock_schema = MagicMock()
    mock_schema.model_validate = MagicMock(return_value="validated")
    mocker.patch("app.api.v1.user_allotment.UserAllotmentRead", mock_schema)
    result = await user_allotment.update_user_allotment(
        mock_request, mock_allotment, mock_db, mock_current_user
    )
    assert result == "validated"
