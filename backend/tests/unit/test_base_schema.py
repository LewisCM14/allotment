from app.api.schemas import base_schema


def test_base_schema_fields():
    schema = base_schema.SecureBaseModel()
    assert hasattr(schema, "dict")
    assert hasattr(schema, "json")
