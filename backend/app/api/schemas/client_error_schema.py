"""
Client Error Schema
"""

from typing import Any, Dict

from pydantic import BaseModel, Field


class ClientErrorLog(BaseModel):
    error: str
    details: Dict[str, Any] | None = Field(default_factory=lambda: {})
