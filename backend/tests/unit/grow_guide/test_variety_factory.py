"""
Test Variety Factory
"""

from uuid import uuid4

import pytest

from app.api.factories.variety_factory import (
    VarietyFactory,
    VarietyFactoryValidationError,
)
from app.api.schemas.grow_guide.variety_schema import VarietyCreate


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
        "water_days": [],
    }
    base_data.update(overrides)
    return VarietyCreate(**base_data)


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
