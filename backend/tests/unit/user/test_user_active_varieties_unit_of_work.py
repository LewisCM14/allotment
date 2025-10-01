import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.api.factories.user_active_variety_factory import UserActiveVarietyFactory
from app.api.middleware.exception_handler import (
    BusinessLogicError,
    ResourceNotFoundError,
)
from app.api.services.user.user_active_varieties_unit_of_work import (
    UserActiveVarietiesUnitOfWork,
)
from tests.test_helpers import make_user_active_variety


class TestUserActiveVarietiesUnitOfWork:
    @pytest.fixture
    def uow(self, mock_db):
        instance = UserActiveVarietiesUnitOfWork(mock_db)
        instance.user_repo = AsyncMock()
        instance.variety_repo = AsyncMock()
        return instance

    @pytest.mark.asyncio
    async def test_aenter_returns_self(self, uow, mocker):
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        result = await uow.__aenter__()
        assert result is uow
        mock_logger.debug.assert_called_once_with(
            "Starting user active varieties unit of work",
            request_id=uow.request_id,
            transaction="begin",
        )

    @pytest.mark.asyncio
    async def test_aexit_commits_on_success(self, uow, mocker):
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.log_timing"
        )
        await uow.__aexit__(None, None, None)
        uow.db.commit.assert_called_once()
        mock_log_timing.assert_called_once_with(
            "user_active_varieties_commit", request_id=uow.request_id
        )
        mock_logger.debug.assert_called_with(
            "Transaction committed successfully",
            transaction="commit",
            request_id=uow.request_id,
        )

    @pytest.mark.asyncio
    async def test_aexit_rolls_back_on_error(self, uow, mocker):
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        await uow.__aexit__(ValueError, ValueError("boom"), None)
        uow.db.rollback.assert_called_once()
        mock_logger.warning.assert_called()
        mock_logger.debug.assert_called_with(
            "Transaction rolled back",
            request_id=uow.request_id,
        )

    @pytest.mark.asyncio
    async def test_get_active_varieties_parses_uuid(self, uow):
        user_id = uuid.uuid4()
        expected = [make_user_active_variety(user_id=user_id) for _ in range(2)]
        uow.user_repo.get_active_varieties.return_value = expected

        result = await uow.get_active_varieties(str(user_id))

        assert result == expected
        uow.user_repo.get_active_varieties.assert_called_once_with(str(user_id))

    @pytest.mark.asyncio
    async def test_get_active_varieties_invalid_uuid(self, uow):
        with pytest.raises(BusinessLogicError):
            await uow.get_active_varieties("not-a-uuid")

    @pytest.mark.asyncio
    async def test_activate_variety_success_creates_association(self, uow, mocker):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        mock_factory = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.UserActiveVarietyFactory"
        )
        association = make_user_active_variety(user_id=user_id, variety_id=variety_id)
        mock_factory.create.return_value = association
        uow.variety_repo.get_variety_owned_by_user.return_value = object()
        uow.user_repo.get_active_variety.return_value = None
        uow.user_repo.add_active_variety.return_value = association

        result = await uow.activate_variety(str(user_id), str(variety_id))

        assert result is association
        uow.variety_repo.get_variety_owned_by_user.assert_called_once_with(
            variety_id, user_id
        )
        uow.user_repo.get_active_variety.assert_called_once_with(user_id, variety_id)
        mock_factory.create.assert_called_once_with(user_id, variety_id)
        uow.user_repo.add_active_variety.assert_called_once_with(association)
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_activate_variety_returns_existing(self, uow, mocker):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        existing = make_user_active_variety(user_id=user_id, variety_id=variety_id)
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        uow.variety_repo.get_variety_owned_by_user.return_value = object()
        uow.user_repo.get_active_variety.return_value = existing

        result = await uow.activate_variety(str(user_id), str(variety_id))

        assert result is existing
        uow.user_repo.add_active_variety.assert_not_called()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_activate_variety_missing_variety(self, uow, mocker):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        uow.variety_repo.get_variety_owned_by_user.return_value = None

        with pytest.raises(ResourceNotFoundError):
            await uow.activate_variety(str(user_id), str(variety_id))

        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_deactivate_variety_success(self, uow, mocker):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        uow.user_repo.delete_active_variety.return_value = True

        await uow.deactivate_variety(str(user_id), str(variety_id))

        uow.user_repo.delete_active_variety.assert_called_once_with(user_id, variety_id)
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_deactivate_variety_not_found(self, uow, mocker):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        uow.user_repo.delete_active_variety.return_value = False

        with pytest.raises(ResourceNotFoundError):
            await uow.deactivate_variety(str(user_id), str(variety_id))

        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_parse_uuid_success(self, uow):
        value = uuid.uuid4()
        result = uow._parse_uuid(str(value), "user_id")
        assert result == value

    @pytest.mark.asyncio
    async def test_parse_uuid_invalid(self, uow):
        with pytest.raises(BusinessLogicError):
            uow._parse_uuid("invalid", "user_id")

    @pytest.mark.asyncio
    async def test_aexit_rolls_back_when_no_exc_value(self, uow, mocker):
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        await uow.__aexit__(ValueError, None, None)
        uow.db.rollback.assert_called_once()
        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_activate_variety_uuid_validation(self, uow):
        with pytest.raises(BusinessLogicError):
            await uow.activate_variety("bad", str(uuid.uuid4()))
        with pytest.raises(BusinessLogicError):
            await uow.activate_variety(str(uuid.uuid4()), "bad")

    @pytest.mark.asyncio
    async def test_deactivate_variety_uuid_validation(self, uow):
        with pytest.raises(BusinessLogicError):
            await uow.deactivate_variety("bad", str(uuid.uuid4()))
        with pytest.raises(BusinessLogicError):
            await uow.deactivate_variety(str(uuid.uuid4()), "bad")

    @pytest.mark.asyncio
    async def test_activate_variety_logs_timing(self, uow, mocker):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        mock_log_timing = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.log_timing"
        )
        uow.variety_repo.get_variety_owned_by_user.return_value = object()
        uow.user_repo.get_active_variety.return_value = None
        association = make_user_active_variety(user_id=user_id, variety_id=variety_id)
        mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.UserActiveVarietyFactory.create",
            return_value=association,
        )
        uow.user_repo.add_active_variety.return_value = association

        await uow.activate_variety(str(user_id), str(variety_id))

        mock_log_timing.assert_called_once_with(
            "uow_activate_variety",
            user_id=str(user_id),
            variety_id=str(variety_id),
            request_id=uow.request_id,
        )

    @pytest.mark.asyncio
    async def test_deactivate_variety_logs_timing(self, uow, mocker):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        mock_log_timing = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.log_timing"
        )
        uow.user_repo.delete_active_variety.return_value = True

        await uow.deactivate_variety(str(user_id), str(variety_id))

        mock_log_timing.assert_called_once_with(
            "uow_deactivate_variety",
            user_id=str(user_id),
            variety_id=str(variety_id),
            request_id=uow.request_id,
        )

    @pytest.mark.asyncio
    async def test_get_active_varieties_logs_timing(self, uow, mocker):
        user_id = uuid.uuid4()
        mock_log_timing = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.log_timing"
        )
        uow.user_repo.get_active_varieties.return_value = []

        await uow.get_active_varieties(str(user_id))

        mock_log_timing.assert_called_once_with(
            "uow_get_active_varieties",
            request_id=uow.request_id,
            user_id=str(user_id),
        )

    @pytest.mark.asyncio
    async def test_activate_variety_existing_does_not_call_factory(self, uow, mocker):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        existing = make_user_active_variety(user_id=user_id, variety_id=variety_id)
        mock_factory = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.UserActiveVarietyFactory"
        )
        uow.variety_repo.get_variety_owned_by_user.return_value = object()
        uow.user_repo.get_active_variety.return_value = existing

        await uow.activate_variety(str(user_id), str(variety_id))

        mock_factory.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_deactivate_variety_not_found_logs_warning(self, uow, mocker):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        uow.user_repo.delete_active_variety.return_value = False

        with pytest.raises(ResourceNotFoundError):
            await uow.deactivate_variety(str(user_id), str(variety_id))

        mock_logger.warning.assert_called_with(
            "Attempted to deactivate non-existent active variety",
            user_id=str(user_id),
            variety_id=str(variety_id),
            request_id=uow.request_id,
        )

    @pytest.mark.asyncio
    async def test_activate_variety_returns_existing_logs_info(self, uow, mocker):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        existing = make_user_active_variety(user_id=user_id, variety_id=variety_id)
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        uow.variety_repo.get_variety_owned_by_user.return_value = object()
        uow.user_repo.get_active_variety.return_value = existing

        result = await uow.activate_variety(str(user_id), str(variety_id))

        assert result is existing
        mock_logger.info.assert_called_with(
            "Variety already active for user",
            user_id=str(user_id),
            variety_id=str(variety_id),
            request_id=uow.request_id,
        )

    @pytest.mark.asyncio
    async def test_activate_variety_creates_logs_info(self, uow, mocker):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        association = make_user_active_variety(user_id=user_id, variety_id=variety_id)
        mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.UserActiveVarietyFactory.create",
            return_value=association,
        )
        uow.variety_repo.get_variety_owned_by_user.return_value = object()
        uow.user_repo.get_active_variety.return_value = None
        uow.user_repo.add_active_variety.return_value = association

        await uow.activate_variety(str(user_id), str(variety_id))

        mock_logger.info.assert_called_with(
            "User active variety created",
            user_id=str(user_id),
            variety_id=str(variety_id),
            request_id=uow.request_id,
        )

    @pytest.mark.asyncio
    async def test_get_active_varieties_invalid_uuid_logs_debug(self, uow, mocker):
        mock_logger = mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.logger"
        )
        with pytest.raises(BusinessLogicError):
            await uow.get_active_varieties("bad")
        mock_logger.debug.assert_called_with(
            "Invalid UUID format received",
            field="user_id",
            value="bad",
            request_id=uow.request_id,
        )

    @pytest.mark.asyncio
    async def test_activate_variety_propagates_existing_factory_timestamp(
        self, uow, mocker
    ):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        now = datetime.now(UTC)
        association = make_user_active_variety(
            user_id=user_id, variety_id=variety_id, activated_at=now
        )
        mocker.patch(
            "app.api.services.user.user_active_varieties_unit_of_work.UserActiveVarietyFactory.create",
            return_value=association,
        )
        uow.variety_repo.get_variety_owned_by_user.return_value = object()
        uow.user_repo.get_active_variety.return_value = None
        uow.user_repo.add_active_variety.return_value = association

        result = await uow.activate_variety(str(user_id), str(variety_id))

        assert result.activated_at == now

    @pytest.mark.asyncio
    async def test_activate_variety_existing_does_not_update_timestamp(self, uow):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        old_time = datetime.now(UTC) - timedelta(days=1)
        existing = make_user_active_variety(
            user_id=user_id, variety_id=variety_id, activated_at=old_time
        )
        uow.variety_repo.get_variety_owned_by_user.return_value = object()
        uow.user_repo.get_active_variety.return_value = existing

        result = await uow.activate_variety(str(user_id), str(variety_id))

        assert result.activated_at == old_time


@pytest.mark.asyncio
async def test_initialization_binds_repositories(mock_db, mocker):
    mock_request_var = mocker.patch(
        "app.api.services.user.user_active_varieties_unit_of_work.request_id_ctx_var"
    )
    mock_request_var.get.return_value = "req-1"
    mock_user_repo = mocker.patch(
        "app.api.services.user.user_active_varieties_unit_of_work.UserRepository"
    )
    mock_variety_repo = mocker.patch(
        "app.api.services.user.user_active_varieties_unit_of_work.VarietyRepository"
    )

    uow = UserActiveVarietiesUnitOfWork(mock_db)

    assert uow.db is mock_db
    assert uow.request_id == "req-1"
    mock_user_repo.assert_called_once_with(mock_db)
    mock_variety_repo.assert_called_once_with(mock_db)


class TestUserActiveVarietyFactory:
    @pytest.fixture(autouse=True)
    def _patch_request_ctx(self, mocker):
        request_ctx = mocker.patch(
            "app.api.factories.user_active_variety_factory.request_id_ctx_var"
        )
        request_ctx.get.return_value = "factory-test-req"
        return request_ctx

    @pytest.mark.asyncio
    async def test_create_success_assigns_ids(self, mocker):
        mock_logger = mocker.patch(
            "app.api.factories.user_active_variety_factory.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.factories.user_active_variety_factory.log_timing"
        )
        mock_log_timing.return_value.__enter__.return_value = None
        mock_log_timing.return_value.__exit__.return_value = False

        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()

        association = UserActiveVarietyFactory.create(user_id, variety_id)

        assert association.user_id == user_id
        assert association.variety_id == variety_id
        mock_log_timing.assert_called_once_with(
            "create_user_active_variety", request_id="factory-test-req"
        )
        mock_logger.info.assert_called_once()

    @pytest.mark.parametrize(
        "user_value,variety_value",
        [
            ("not-uuid", uuid.uuid4()),
            (uuid.uuid4(), "not-uuid"),
            ("not-uuid", "also-bad"),
        ],
    )
    def test_create_invalid_inputs_raise_business_logic_error(
        self, user_value, variety_value
    ):
        with pytest.raises(BusinessLogicError) as exc_info:
            UserActiveVarietyFactory.create(user_value, variety_value)

        assert exc_info.value.status_code == 400
        assert "must be valid UUID" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_create_handles_internal_failure(self, mocker):
        mock_logger = mocker.patch(
            "app.api.factories.user_active_variety_factory.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.factories.user_active_variety_factory.log_timing"
        )
        mock_log_timing.return_value.__enter__.return_value = None
        mock_log_timing.return_value.__exit__.return_value = False

        failing_cls = mocker.patch(
            "app.api.factories.user_active_variety_factory.UserActiveVariety"
        )
        failing_cls.side_effect = RuntimeError("boom")

        with pytest.raises(BusinessLogicError) as exc_info:
            UserActiveVarietyFactory.create(uuid.uuid4(), uuid.uuid4())

        assert exc_info.value.status_code == 500
        assert "Unable to create user active variety association" in str(
            exc_info.value.message
        )
        mock_logger.error.assert_called_once()
