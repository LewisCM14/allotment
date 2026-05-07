"""
Client Error Schema
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


def _check_depth(obj: Any, max_depth: int = 5, _current: int = 0) -> None:
    if _current > max_depth:
        raise ValueError(f"details nesting exceeds maximum depth of {max_depth}")
    if isinstance(obj, dict):
        for value in obj.values():
            _check_depth(value, max_depth, _current + 1)
    elif isinstance(obj, list):
        for item in obj:
            _check_depth(item, max_depth, _current + 1)


class ClientErrorLog(BaseModel):
    error: str = Field(..., max_length=10_000)
    details: dict[str, Any] | None = Field(default_factory=dict)

    @field_validator("details")
    @classmethod
    def validate_details_depth(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if value is not None:
            _check_depth(value)
        return value
