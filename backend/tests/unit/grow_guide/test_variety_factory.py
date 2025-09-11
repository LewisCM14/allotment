"""
Test Variety Factory
"""

from unittest.mock import patch
from uuid import uuid4

import pytest

from app.api.factories.variety_factory import (
    VarietyFactory,
    VarietyFactoryValidationError,
)
from app.api.middleware.exception_handler import BusinessLogicError
from app.api.schemas.grow_guide.variety_schema import VarietyCreate, VarietyUpdate
from tests.test_helpers import make_variety


def create_valid_variety_data(**overrides):
    """Helper function to create valid VarietyCreate data."""
    base_data = {
        "variety_name": "Test Tomato",
        "family_id": uuid4(),
        "lifecycle_id": uuid4(),
        "sow_week_start_id": uuid4(),
        "sow_week_end_id": uuid4(),
        "planting_conditions_id": uuid4(),
        "soil_ph": 6.5,
        "plant_depth_cm": 2,
        "plant_space_cm": 30,
        "water_frequency_id": uuid4(),
        "harvest_week_start_id": uuid4(),
        "harvest_week_end_id": uuid4(),
        "is_public": False,
    }
    base_data.update(overrides)
    return VarietyCreate(**base_data)


def create_valid_variety_update_data(**overrides):
    """Helper function to create valid VarietyUpdate data."""
    base_data = {
        "variety_name": "Updated Tomato",
        "family_id": uuid4(),
        "lifecycle_id": uuid4(),
        "soil_ph": 7.0,
        "plant_depth_cm": 3,
    }
    base_data.update(overrides)
    return VarietyUpdate(**base_data)


class TestVarietyFactory:
    def test_create_variety_happy_path(self):
        """Test successful variety creation."""
        user_id = uuid4()
        lifecycle_id = uuid4()
        planting_conditions_id = uuid4()

        variety_data = create_valid_variety_data(
            lifecycle_id=lifecycle_id,
            planting_conditions_id=planting_conditions_id,
        )

        variety = VarietyFactory.create_variety(variety_data, user_id)

        assert variety.variety_name == "Test Tomato"
        assert variety.owner_user_id == user_id
        assert variety.lifecycle_id == lifecycle_id
        assert variety.planting_conditions_id == planting_conditions_id
        assert variety.is_public is False

    def test_create_variety_with_transplant_weeks_both_provided(self):
        """Test variety creation with both transplant weeks provided."""
        user_id = uuid4()
        lifecycle_id = uuid4()
        planting_conditions_id = uuid4()
        transplant_start_id = uuid4()
        transplant_end_id = uuid4()

        variety_data = create_valid_variety_data(
            lifecycle_id=lifecycle_id,
            planting_conditions_id=planting_conditions_id,
            transplant_week_start_id=transplant_start_id,
            transplant_week_end_id=transplant_end_id,
        )

        variety = VarietyFactory.create_variety(variety_data, user_id)

        assert variety.transplant_week_start_id == transplant_start_id
        assert variety.transplant_week_end_id == transplant_end_id

    def test_create_variety_transplant_weeks_validation_start_only(self):
        """Test validation fails when only transplant start week is provided."""
        user_id = uuid4()
        transplant_start_id = uuid4()

        variety_data = create_valid_variety_data(
            transplant_week_start_id=transplant_start_id,
            # transplant_week_end_id not provided
        )

        with pytest.raises(VarietyFactoryValidationError) as exc_info:
            VarietyFactory.create_variety(variety_data, user_id)

        assert (
            "transplant week start and end must be provided together"
            in str(exc_info.value).lower()
        )

    def test_create_variety_transplant_weeks_validation_end_only(self):
        """Test validation fails when only transplant end week is provided."""
        user_id = uuid4()
        transplant_end_id = uuid4()

        variety_data = create_valid_variety_data(
            # transplant_week_start_id not provided
            transplant_week_end_id=transplant_end_id,
        )

        with pytest.raises(VarietyFactoryValidationError) as exc_info:
            VarietyFactory.create_variety(variety_data, user_id)

        assert (
            "transplant week start and end must be provided together"
            in str(exc_info.value).lower()
        )

    def test_create_variety_prune_weeks_validation_start_only(self):
        """Test validation fails when only prune start week is provided."""
        user_id = uuid4()
        prune_start_id = uuid4()

        variety_data = create_valid_variety_data(
            prune_week_start_id=prune_start_id,
            # prune_week_end_id not provided
        )

        with pytest.raises(VarietyFactoryValidationError) as exc_info:
            VarietyFactory.create_variety(variety_data, user_id)

        assert (
            "prune week start and end must be provided together"
            in str(exc_info.value).lower()
        )

    def test_create_variety_feed_details_validation_partial(self):
        """Test validation fails when feed details are partially provided."""
        user_id = uuid4()
        feed_id = uuid4()

        variety_data = create_valid_variety_data(
            feed_id=feed_id,
            # feed_week_start_id and feed_frequency_id not provided
        )

        with pytest.raises(VarietyFactoryValidationError) as exc_info:
            VarietyFactory.create_variety(variety_data, user_id)

        assert (
            "feed id, feed week start, and feed frequency must all be provided together"
            in str(exc_info.value).lower()
        )

    def test_create_variety_feed_details_all_provided(self):
        """Test variety creation with all feed details provided."""
        user_id = uuid4()
        feed_id = uuid4()
        feed_week_start_id = uuid4()
        feed_frequency_id = uuid4()

        variety_data = create_valid_variety_data(
            feed_id=feed_id,
            feed_week_start_id=feed_week_start_id,
            feed_frequency_id=feed_frequency_id,
        )

        variety = VarietyFactory.create_variety(variety_data, user_id)

        assert variety.feed_id == feed_id
        assert variety.feed_week_start_id == feed_week_start_id
        assert variety.feed_frequency_id == feed_frequency_id

    def test_create_water_days(self):
        """Test water days creation."""
        variety_id = uuid4()
        day_id_1 = uuid4()
        day_id_2 = uuid4()

        water_days_data = [
            {"day_id": day_id_1},
            {"day_id": day_id_2},
        ]

        water_days = VarietyFactory.create_water_days(variety_id, water_days_data)

        assert len(water_days) == 2
        assert water_days[0].variety_id == variety_id
        assert water_days[0].day_id == day_id_1
        assert water_days[1].variety_id == variety_id
        assert water_days[1].day_id == day_id_2

    def test_variety_factory_validation_error_to_dict(self):
        """Test VarietyFactoryValidationError to_dict method."""
        error = VarietyFactoryValidationError(
            message="Test error message", field="test_field", status_code=422
        )

        error_dict = error.to_dict()

        assert error_dict["detail"] == "Test error message (Field: test_field)"
        assert error_dict["field"] == "test_field"
        assert error_dict["status_code"] == 422
        assert "error_code" in error_dict

    @patch("app.api.factories.variety_factory.log_timing")
    @patch("app.api.factories.variety_factory.logger")
    def test_create_variety_exception_handling(self, mock_logger, mock_log_timing):
        """Test exception handling in create_variety method."""
        user_id = uuid4()

        # Create invalid data that will cause an exception
        with patch(
            "app.api.factories.variety_factory.VarietyFactory._validate_transplant_weeks"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Unexpected error")

            variety_data = create_valid_variety_data()

            with pytest.raises(BusinessLogicError) as exc_info:
                VarietyFactory.create_variety(variety_data, user_id)

            assert "An unexpected error occurred during variety creation" in str(
                exc_info.value
            )
            assert exc_info.value.status_code == 500

    @patch("app.api.factories.variety_factory.log_timing")
    @patch("app.api.factories.variety_factory.logger")
    def test_create_water_days_exception_handling(self, mock_logger, mock_log_timing):
        """Test exception handling in create_water_days method."""
        variety_id = uuid4()

        # Simulate an exception during water days creation
        with patch(
            "app.api.factories.variety_factory.VarietyWaterDay"
        ) as mock_water_day:
            mock_water_day.side_effect = Exception("Database error")

            water_days_data = [{"day_id": uuid4()}]

            with pytest.raises(BusinessLogicError) as exc_info:
                VarietyFactory.create_water_days(variety_id, water_days_data)

            assert "An unexpected error occurred during water days creation" in str(
                exc_info.value
            )
            assert exc_info.value.status_code == 500


class TestVarietyFactoryUpdateVariety:
    """Test suite for update_variety method."""

    def test_update_variety_basic_fields(self):
        """Test updating basic variety fields."""
        user_id = uuid4()

        # Create original variety
        original_variety = make_variety(owner_user_id=user_id)
        original_variety.variety_name = "Original Tomato"
        original_variety.soil_ph = 6.5

        # Create update data
        update_data = create_valid_variety_update_data(
            variety_name="Updated Tomato", soil_ph=7.0
        )

        # Update the variety
        updated_variety = VarietyFactory.update_variety(original_variety, update_data)

        assert updated_variety.variety_name == "Updated Tomato"
        assert updated_variety.soil_ph == 7.0
        assert updated_variety.owner_user_id == user_id

    def test_update_variety_partial_update(self):
        """Test updating only some fields."""
        user_id = uuid4()

        # Create original variety
        original_variety = make_variety(owner_user_id=user_id)
        original_variety.variety_name = "Original Tomato"
        original_variety.soil_ph = 6.5
        original_variety.plant_depth_cm = 2

        # Create update data with only some fields
        update_data = VarietyUpdate(
            variety_name="Updated Tomato",
            # soil_ph not provided - should keep original
            plant_depth_cm=3,
        )

        # Update the variety
        updated_variety = VarietyFactory.update_variety(original_variety, update_data)

        assert updated_variety.variety_name == "Updated Tomato"
        assert updated_variety.soil_ph == 6.5  # Should keep original value
        assert updated_variety.plant_depth_cm == 3

    def test_update_variety_all_conditional_fields(self):
        """Test updating all conditional fields to ensure coverage."""
        user_id = uuid4()

        # Create original variety
        original_variety = make_variety(owner_user_id=user_id)

        # Create update data with all possible fields
        update_data = VarietyUpdate(
            variety_name="Updated Name",
            family_id=uuid4(),
            lifecycle_id=uuid4(),
            sow_week_start_id=uuid4(),
            sow_week_end_id=uuid4(),
            transplant_week_start_id=uuid4(),
            transplant_week_end_id=uuid4(),
            planting_conditions_id=uuid4(),
            soil_ph=7.5,
            row_width_cm=25.0,
            plant_depth_cm=4,
            plant_space_cm=35,
            feed_id=uuid4(),
            feed_week_start_id=uuid4(),
            feed_frequency_id=uuid4(),
            water_frequency_id=uuid4(),
            high_temp_degrees=30.0,
            high_temp_water_frequency_id=uuid4(),
            harvest_week_start_id=uuid4(),
            harvest_week_end_id=uuid4(),
            prune_week_start_id=uuid4(),
            prune_week_end_id=uuid4(),
            notes="Updated notes",
            is_public=True,
        )

        # Update the variety
        updated_variety = VarietyFactory.update_variety(original_variety, update_data)

        # Verify all fields were updated
        assert updated_variety.variety_name == "Updated Name"
        assert updated_variety.family_id == update_data.family_id
        assert updated_variety.lifecycle_id == update_data.lifecycle_id
        assert updated_variety.soil_ph == 7.5
        assert updated_variety.row_width_cm == 25.0
        assert updated_variety.plant_depth_cm == 4
        assert updated_variety.plant_space_cm == 35
        assert updated_variety.notes == "Updated notes"
        assert updated_variety.is_public is True

    def test_update_variety_validation_errors(self):
        """Test that validation errors are raised during update."""
        user_id = uuid4()

        # Create original variety
        original_variety = make_variety(owner_user_id=user_id)

        # Create update data with invalid transplant weeks (only start provided)
        update_data = VarietyUpdate(
            transplant_week_start_id=uuid4(),
            # transplant_week_end_id not provided - should fail validation
        )

        with pytest.raises(VarietyFactoryValidationError) as exc_info:
            VarietyFactory.update_variety(original_variety, update_data)

        assert (
            "transplant week start and end must be provided together"
            in str(exc_info.value).lower()
        )

    def test_update_variety_feed_validation_errors(self):
        """Test feed validation errors during update."""
        user_id = uuid4()

        # Create original variety
        original_variety = make_variety(owner_user_id=user_id)

        # Create update data with partial feed details
        update_data = VarietyUpdate(
            feed_id=uuid4(),
            feed_week_start_id=uuid4(),
            # feed_frequency_id not provided - should fail validation
        )

        with pytest.raises(VarietyFactoryValidationError) as exc_info:
            VarietyFactory.update_variety(original_variety, update_data)

        assert (
            "feed id, feed week start, and feed frequency must all be provided together"
            in str(exc_info.value).lower()
        )

    @patch("app.api.factories.variety_factory.log_timing")
    @patch("app.api.factories.variety_factory.logger")
    def test_update_variety_validation_error_handling(
        self, mock_logger, mock_log_timing
    ):
        """Test validation error handling in update_variety."""
        user_id = uuid4()

        # Create original variety
        original_variety = make_variety(owner_user_id=user_id)

        # Create update data that will cause validation error
        update_data = VarietyUpdate(
            transplant_week_start_id=uuid4(),
            # Missing transplant_week_end_id
        )

        with pytest.raises(VarietyFactoryValidationError):
            VarietyFactory.update_variety(original_variety, update_data)

        # Verify logger was called
        mock_logger.error.assert_called()

    @patch("app.api.factories.variety_factory.log_timing")
    @patch("app.api.factories.variety_factory.logger")
    def test_update_variety_unexpected_exception_handling(
        self, mock_logger, mock_log_timing
    ):
        """Test unexpected exception handling in update_variety."""
        user_id = uuid4()

        # Create original variety
        original_variety = make_variety(owner_user_id=user_id)

        # Mock validation to raise unexpected exception
        with patch(
            "app.api.factories.variety_factory.VarietyFactory._validate_transplant_weeks"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Unexpected error")

            update_data = VarietyUpdate(variety_name="Test")

            with pytest.raises(BusinessLogicError) as exc_info:
                VarietyFactory.update_variety(original_variety, update_data)

            assert "An unexpected error occurred during variety update" in str(
                exc_info.value
            )
            assert exc_info.value.status_code == 500

            # Verify logger was called
            mock_logger.critical.assert_called()
