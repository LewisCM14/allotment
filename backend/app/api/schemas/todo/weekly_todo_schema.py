"""
Weekly Todo Schema
- Defines response structures for weekly todo lists.
- Organizes tasks by week and day for user's active varieties.
"""

from typing import Dict, List
from uuid import UUID

from pydantic import ConfigDict, Field

from app.api.schemas.base_schema import SecureBaseModel


class VarietyTaskDetail(SecureBaseModel):
    """Details about a variety in a task list."""

    variety_id: UUID
    variety_name: str
    family_name: str

    model_config = ConfigDict(from_attributes=True)


class FeedTaskDetail(SecureBaseModel):
    """Details about a feeding task, grouped by feed type."""

    feed_id: UUID
    feed_name: str
    varieties: List[VarietyTaskDetail]

    model_config = ConfigDict(from_attributes=True)


class DailyTasks(SecureBaseModel):
    """Tasks for a specific day of the week."""

    day_id: UUID
    day_number: int
    day_name: str
    feed_tasks: List[FeedTaskDetail] = Field(
        default_factory=list, description="Feeding tasks grouped by feed type"
    )
    water_tasks: List[VarietyTaskDetail] = Field(
        default_factory=list, description="Varieties that need watering"
    )

    model_config = ConfigDict(from_attributes=True)


class WeeklyTasks(SecureBaseModel):
    """Tasks for the entire week."""

    sow_tasks: List[VarietyTaskDetail] = Field(
        default_factory=list, description="Varieties that can be sown this week"
    )
    transplant_tasks: List[VarietyTaskDetail] = Field(
        default_factory=list, description="Varieties that can be transplanted this week"
    )
    harvest_tasks: List[VarietyTaskDetail] = Field(
        default_factory=list, description="Varieties that can be harvested this week"
    )
    prune_tasks: List[VarietyTaskDetail] = Field(
        default_factory=list, description="Varieties that need pruning this week"
    )
    compost_tasks: List[VarietyTaskDetail] = Field(
        default_factory=list,
        description="Varieties that can be composted (end of lifecycle)",
    )

    model_config = ConfigDict(from_attributes=True)


class WeeklyTodoRead(SecureBaseModel):
    """Complete weekly todo list with both weekly and daily tasks."""

    week_id: UUID
    week_number: int
    week_start_date: str
    week_end_date: str
    weekly_tasks: WeeklyTasks
    daily_tasks: Dict[int, DailyTasks] = Field(
        default_factory=dict, description="Daily tasks mapped by day number (1-7)"
    )

    model_config = ConfigDict(from_attributes=True)
