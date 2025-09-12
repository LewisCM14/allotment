import uuid

from app.api.schemas.grow_guide.variety_schema import VarietyCreate, VarietyUpdate


def test_variety_create_empty_string_optional_uuid_fields_coerced():
    base_uuid = uuid.uuid4()
    data = {
        "variety_name": "Test",
        "family_id": str(base_uuid),
        "lifecycle_id": str(base_uuid),
        "sow_week_start_id": str(base_uuid),
        "sow_week_end_id": str(base_uuid),
        "planting_conditions_id": str(base_uuid),
        "soil_ph": 6.5,
        "plant_depth_cm": 2,
        "plant_space_cm": 30,
        "water_frequency_id": str(base_uuid),
        "harvest_week_start_id": str(base_uuid),
        "harvest_week_end_id": str(base_uuid),
        # Optional UUID fields submitted as empty strings
        "transplant_week_start_id": "",
        "transplant_week_end_id": "",
        "feed_id": "",
        "feed_week_start_id": "",
        "feed_frequency_id": "",
        "high_temp_water_frequency_id": "",
        "prune_week_start_id": "",
        "prune_week_end_id": "",
        "notes": "Some notes",
        "is_public": False,
    }
    model = VarietyCreate(**data)
    assert model.transplant_week_start_id is None
    assert model.transplant_week_end_id is None
    assert model.feed_id is None
    assert model.feed_week_start_id is None
    assert model.feed_frequency_id is None
    assert model.high_temp_water_frequency_id is None
    assert model.prune_week_start_id is None
    assert model.prune_week_end_id is None


def test_variety_update_empty_string_coerced():
    data = {
        "variety_name": "Updated",
        "prune_week_start_id": "",
        "prune_week_end_id": "",
        "feed_id": "",
        "water_frequency_id": "",
    }
    model = VarietyUpdate(**data)
    assert model.prune_week_start_id is None
    assert model.prune_week_end_id is None
    assert model.feed_id is None
    # Explicit empty string for optional water_frequency_id should become None
    assert model.water_frequency_id is None
