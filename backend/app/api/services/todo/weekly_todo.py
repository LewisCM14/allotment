"""
Weekly Todo Unit of Work
- Coordinates retrieval of weekly and daily tasks for a user's active varieties.
- Aggregates data from Week, Day, Variety, UserActiveVariety, Feed, and Frequency tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from types import TracebackType
from typing import Any, Dict, List, Optional, Type, Union

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.core.logging import log_timing
from app.api.middleware.error_handler import translate_db_exceptions
from app.api.middleware.exception_handler import (
    BusinessLogicError,
    ResourceNotFoundError,
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models.enums import LifecycleType
from app.api.models.grow_guide.calendar_model import Week
from app.api.models.grow_guide.guide_options_model import Frequency
from app.api.models.grow_guide.variety_model import Variety
from app.api.models.user.user_model import UserActiveVariety, UserFeedDay
from app.api.repositories.grow_guide.day_repository import DayRepository
from app.api.repositories.grow_guide.week_repository import WeekRepository
from app.api.repositories.user.user_repository import UserRepository

logger = structlog.get_logger()


class WeeklyTodoUnitOfWork:
    """Unit of Work for managing weekly todo operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.week_repo = WeekRepository(db)
        self.day_repo = DayRepository(db)
        self.request_id = request_id_ctx_var.get()

    async def __aenter__(self) -> "WeeklyTodoUnitOfWork":
        logger.debug(
            "Starting weekly todo unit of work",
            request_id=self.request_id,
            transaction="begin",
        )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        log_context = {"request_id": self.request_id}

        if exc_type:
            if exc_value:
                sanitized_error = sanitize_error_message(str(exc_value))
                logger.warning(
                    "Rolling back transaction due to error",
                    error=sanitized_error,
                    error_type=exc_type.__name__,
                    **log_context,
                )
            else:
                logger.warning(
                    "Rolling back transaction due to unknown error",
                    error_type=str(exc_type),
                    **log_context,
                )
            await self.db.rollback()
            logger.debug("Transaction rolled back", **log_context)
        else:
            try:
                with log_timing("weekly_todo_commit", **log_context):
                    await self.db.commit()
                    logger.debug(
                        "Transaction committed successfully",
                        transaction="commit",
                        **log_context,
                    )
            except IntegrityError as exc:  # pragma: no cover - defensive guard
                await self.db.rollback()
                sanitized_error = sanitize_error_message(str(exc))
                logger.error(
                    "Integrity error committing weekly todo",
                    error=sanitized_error,
                    error_type="IntegrityError",
                    **log_context,
                )
                raise

    @translate_db_exceptions
    async def get_weekly_todo(
        self, user_id: str, week_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get weekly and daily tasks for a user's active varieties.

        Args:
            user_id: The user's UUID as a string
            week_number: Optional week number (1-52). If None, uses current week.

        Returns:
            Dictionary containing week info, weekly tasks, and daily tasks
        """
        parsed_user_id = self._parse_uuid(user_id, "user_id")

        log_context = {
            "user_id": user_id,
            "week_number": week_number,
            "request_id": self.request_id,
        }

        with log_timing("uow_get_weekly_todo", **log_context):
            # Get the target week
            if week_number is None:
                week_number = self._get_current_week_number()

            week = await self._get_week_by_number(week_number)
            if week is None:
                raise ResourceNotFoundError("Week", str(week_number))

            # Get user's active varieties with all necessary relationships
            active_varieties = await self._get_user_active_varieties(parsed_user_id)

            if not active_varieties:
                logger.info("No active varieties for user", **log_context)
                return self._create_empty_todo_response(week)

            # Build weekly tasks
            weekly_tasks = await self._build_weekly_tasks(
                active_varieties, week.week_id
            )

            # Build daily tasks
            daily_tasks = await self._build_daily_tasks(
                parsed_user_id, active_varieties, week.week_number
            )

            logger.info(
                "Weekly todo retrieved successfully",
                active_varieties_count=len(active_varieties),
                **log_context,
            )

            return {
                "week_id": week.week_id,
                "week_number": week.week_number,
                "week_start_date": week.week_start_date,
                "week_end_date": week.week_end_date,
                "weekly_tasks": weekly_tasks,
                "daily_tasks": daily_tasks,
            }

    async def _get_week_by_number(self, week_number: int) -> Optional[Week]:
        """Get a week by its number."""
        with log_timing("db_get_week_by_number", request_id=self.request_id):
            stmt = select(Week).where(Week.week_number == week_number)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

    async def _get_user_active_varieties(self, user_id: uuid.UUID) -> List[Variety]:
        """Get all active varieties for a user with necessary relationships loaded."""
        with log_timing("db_get_user_active_varieties", request_id=self.request_id):
            stmt = (
                select(Variety)
                .join(
                    UserActiveVariety,
                    UserActiveVariety.variety_id == Variety.variety_id,
                )
                .options(
                    selectinload(Variety.family),
                    selectinload(Variety.lifecycle),
                    selectinload(Variety.feed),
                    selectinload(Variety.feed_frequency),
                    selectinload(Variety.water_frequency).selectinload(
                        Frequency.default_days
                    ),
                )
                .where(UserActiveVariety.user_id == user_id)
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().unique().all())

    async def _build_weekly_tasks(
        self, active_varieties: List[Variety], week_id: uuid.UUID
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Build weekly tasks from active varieties."""
        tasks: Dict[str, List[Dict[str, Any]]] = {
            "sow_tasks": [],
            "transplant_tasks": [],
            "harvest_tasks": [],
            "prune_tasks": [],
            "compost_tasks": [],
        }

        # Get the current week number for week range comparisons
        current_week = await self._get_week_by_id(week_id)
        if not current_week:
            return tasks

        # Pre-load all week IDs to week numbers for efficient lookup
        week_id_to_number = await self._get_week_id_to_number_map(active_varieties)

        for variety in active_varieties:
            variety_info = {
                "variety_id": variety.variety_id,
                "variety_name": variety.variety_name,
                "family_name": variety.family.family_name if variety.family else "",
            }

            # Check if this week is within sowing period
            if await self._is_week_in_range_by_number(
                current_week.week_number,
                variety.sow_week_start_id,
                variety.sow_week_end_id,
                week_id_to_number,
            ):
                tasks["sow_tasks"].append(variety_info)

            # Check transplant period
            if variety.transplant_week_start_id and variety.transplant_week_end_id:
                if await self._is_week_in_range_by_number(
                    current_week.week_number,
                    variety.transplant_week_start_id,
                    variety.transplant_week_end_id,
                    week_id_to_number,
                ):
                    tasks["transplant_tasks"].append(variety_info)

            # Check harvest period
            if await self._is_week_in_range_by_number(
                current_week.week_number,
                variety.harvest_week_start_id,
                variety.harvest_week_end_id,
                week_id_to_number,
            ):
                tasks["harvest_tasks"].append(variety_info)

            # Check prune period
            if variety.prune_week_start_id and variety.prune_week_end_id:
                if await self._is_week_in_range_by_number(
                    current_week.week_number,
                    variety.prune_week_start_id,
                    variety.prune_week_end_id,
                    week_id_to_number,
                ):
                    tasks["prune_tasks"].append(variety_info)

            # Check if variety should be composted based on lifecycle
            if await self._should_compost_variety(
                variety, current_week.week_number, week_id_to_number
            ):
                tasks["compost_tasks"].append(variety_info)

        return tasks

    async def _build_daily_tasks(
        self,
        user_id: uuid.UUID,
        active_varieties: List[Variety],
        week_number: int,
    ) -> Dict[int, Dict[str, Any]]:
        """Build daily tasks for the week."""
        daily_tasks: Dict[int, Dict[str, Any]] = {}

        # Get all days
        all_days = await self.day_repo.get_all_days()

        # Get user's feed preferences
        user_feed_days = await self._get_user_feed_days(user_id)

        # Pre-load map of week_id -> week_number for range checks
        week_id_to_number = await self._get_week_id_to_number_map(active_varieties)

        for day in all_days:
            day_info = {
                "day_id": day.day_id,
                "day_number": day.day_number,
                "day_name": day.day_name,
                "feed_tasks": [],
                "water_tasks": [],
            }

            # Build feed tasks grouped by feed type
            feed_tasks_by_feed = await self._build_feed_tasks_for_day(
                active_varieties, day.day_id, week_number, user_feed_days
            )
            day_info["feed_tasks"] = feed_tasks_by_feed

            # Build water tasks (annuals limited to active season)
            water_tasks = await self._build_water_tasks_for_day(
                active_varieties, day.day_id, week_number, week_id_to_number
            )
            day_info["water_tasks"] = water_tasks

            daily_tasks[day.day_number] = day_info

        return daily_tasks

    async def _get_user_feed_days(
        self, user_id: uuid.UUID
    ) -> Dict[uuid.UUID, uuid.UUID]:
        """Get user's feed day preferences as a mapping of feed_id to day_id."""
        with log_timing("db_get_user_feed_days", request_id=self.request_id):
            stmt = select(UserFeedDay).where(UserFeedDay.user_id == user_id)
            result = await self.db.execute(stmt)
            user_feed_days = result.scalars().all()
            return {ufd.feed_id: ufd.day_id for ufd in user_feed_days}

    async def _build_feed_tasks_for_day(
        self,
        active_varieties: List[Variety],
        day_id: uuid.UUID,
        week_number: int,
        user_feed_days: Dict[uuid.UUID, uuid.UUID],
    ) -> List[Dict[str, Any]]:
        """Build feeding tasks for a specific day, grouped by feed type."""
        feed_groups: Dict[uuid.UUID, Dict[str, Any]] = {}

        for variety in active_varieties:
            # Check if variety needs feeding
            if (
                not variety.feed_id
                or not variety.feed_week_start_id
                or not variety.feed_frequency_id
            ):
                continue

            # Check if this week is within feeding period
            if not await self._is_week_in_feeding_period(
                week_number,
                variety.feed_week_start_id,
                variety.feed_frequency_id,
                variety.harvest_week_end_id,
                variety.lifecycle.lifecycle_name
                if variety.lifecycle
                else LifecycleType.ANNUAL,
            ):
                continue

            # Check if user feeds this type on this day
            user_feed_day = user_feed_days.get(variety.feed_id)
            if user_feed_day != day_id:
                continue

            # Group by feed type
            if variety.feed_id not in feed_groups:
                feed_groups[variety.feed_id] = {
                    "feed_id": variety.feed_id,
                    "feed_name": variety.feed.feed_name if variety.feed else "",
                    "varieties": [],
                }

            feed_groups[variety.feed_id]["varieties"].append(
                {
                    "variety_id": variety.variety_id,
                    "variety_name": variety.variety_name,
                    "family_name": variety.family.family_name if variety.family else "",
                }
            )

        return list(feed_groups.values())

    async def _build_water_tasks_for_day(
        self,
        active_varieties: List[Variety],
        day_id: uuid.UUID,
        week_number: int,
        week_id_to_number: Dict[uuid.UUID, int],
    ) -> List[Dict[str, Any]]:
        """Build watering tasks for a specific day using frequency default days."""
        water_tasks = []

        for variety in active_varieties:
            # Limit annuals to their active season between sow start and harvest end (inclusive)
            if variety.lifecycle:
                lifecycle = self._to_lifecycle_type(variety.lifecycle.lifecycle_name)
                if lifecycle == LifecycleType.ANNUAL:
                    start_num = week_id_to_number.get(variety.sow_week_start_id)
                    end_num = week_id_to_number.get(variety.harvest_week_end_id)

                    # Fallback: fetch missing week numbers
                    if start_num is None or end_num is None:
                        with log_timing(
                            "db_fetch_missing_week_numbers", request_id=self.request_id
                        ):
                            ids: List[uuid.UUID] = []
                            if start_num is None:
                                ids.append(variety.sow_week_start_id)
                            if end_num is None:
                                ids.append(variety.harvest_week_end_id)
                            if ids:
                                stmt = select(Week.week_id, Week.week_number).where(
                                    Week.week_id.in_(ids)
                                )
                                result = await self.db.execute(stmt)
                                for wid, wnum in result.all():
                                    week_id_to_number[wid] = wnum
                                start_num = week_id_to_number.get(
                                    variety.sow_week_start_id
                                )
                                end_num = week_id_to_number.get(
                                    variety.harvest_week_end_id
                                )

                    # If still missing, skip (cannot determine season)
                    if start_num is None or end_num is None:
                        continue

                    # Check if current week in [start, end], handling wrap-around
                    if start_num <= end_num:
                        in_season = start_num <= week_number <= end_num
                    else:
                        in_season = week_number >= start_num or week_number <= end_num

                    if not in_season:
                        continue

            # Check if variety's water frequency includes this day
            if variety.water_frequency and variety.water_frequency.default_days:
                for default_day in variety.water_frequency.default_days:
                    if default_day.day_id == day_id:
                        water_tasks.append(
                            {
                                "variety_id": variety.variety_id,
                                "variety_name": variety.variety_name,
                                "family_name": variety.family.family_name
                                if variety.family
                                else "",
                            }
                        )
                        break  # Only add once per variety

        return water_tasks

    async def _is_week_in_feeding_period(
        self,
        week_number: int,
        feed_week_start_id: uuid.UUID,
        feed_frequency_id: uuid.UUID,
        harvest_week_end_id: uuid.UUID,
        lifecycle_name: Union[LifecycleType, str],
    ) -> bool:
        """
        Check if the given week is within the feeding period.

        For annuals: Feed from feed_week_start until harvest_week_end.
        For perennials/biennials: Feed from feed_week_start onwards (continues across years).

        Frequency determines HOW OFTEN to feed within the period.
        """
        with log_timing("db_check_feeding_period", request_id=self.request_id):
            # Get the start week number
            stmt = select(Week.week_number).where(Week.week_id == feed_week_start_id)
            result = await self.db.execute(stmt)
            start_week_number = result.scalar_one_or_none()

            if start_week_number is None:
                return False

            # Coerce lifecycle to enum for comparisons (handles str inputs)
            lifecycle = self._to_lifecycle_type(lifecycle_name)

            # For annuals, check we haven't passed harvest end
            if lifecycle == LifecycleType.ANNUAL:
                harvest_stmt = select(Week.week_number).where(
                    Week.week_id == harvest_week_end_id
                )
                harvest_result = await self.db.execute(harvest_stmt)
                harvest_end_week = harvest_result.scalar_one_or_none()

                if harvest_end_week is None:
                    return False

                # Handle year wrap-around
                if start_week_number <= harvest_end_week:
                    # Normal case: start week before harvest
                    if (
                        week_number < start_week_number
                        or week_number > harvest_end_week
                    ):
                        return False
                else:
                    # Wrap-around case: harvest crosses year boundary
                    if (
                        week_number < start_week_number
                        and week_number > harvest_end_week
                    ):
                        return False
            else:
                # For perennials/biennials, check we're after start week
                # Handle year wrap-around
                if week_number < start_week_number:
                    # Could be in next year's cycle
                    week_number += 52

            # Get the frequency details
            freq_stmt = select(Frequency).where(
                Frequency.frequency_id == feed_frequency_id
            )
            freq_result = await self.db.execute(freq_stmt)
            frequency = freq_result.scalar_one_or_none()

            if frequency is None:
                return False

            # Calculate weeks since start (handling wrap-around)
            weeks_since_start = week_number - start_week_number
            if weeks_since_start < 0:
                weeks_since_start += 52

            # Interpret frequency_days_per_year as number of feed occurrences per year
            # Examples:
            #   Weekly -> 52  => every 1 week
            #   Fortnightly -> 26 => every 2 weeks
            #   Monthly -> 12 => ~every 4 weeks (rounded)
            #   Yearly -> 1 => every 52 weeks
            occurrences_per_year = max(0, int(frequency.frequency_days_per_year))
            if occurrences_per_year <= 0:
                return False

            if occurrences_per_year >= 52:
                weeks_between_feeds = 1
            else:
                # Round to the nearest whole number of weeks between feeds
                weeks_between_feeds = max(1, int(round(52.0 / occurrences_per_year)))

            # Check if this week aligns with the schedule anchored at start week
            return weeks_since_start % weeks_between_feeds == 0

    async def _get_week_by_id(self, week_id: uuid.UUID) -> Optional[Week]:
        """Get a week by its ID."""
        with log_timing("db_get_week_by_id", request_id=self.request_id):
            stmt = select(Week).where(Week.week_id == week_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

    async def _get_week_id_to_number_map(
        self, active_varieties: List[Variety]
    ) -> Dict[uuid.UUID, int]:
        """Build a map of week IDs to week numbers for all weeks referenced by varieties."""
        week_ids = set()

        for variety in active_varieties:
            week_ids.add(variety.sow_week_start_id)
            week_ids.add(variety.sow_week_end_id)
            week_ids.add(variety.harvest_week_start_id)
            week_ids.add(variety.harvest_week_end_id)

            if variety.transplant_week_start_id:
                week_ids.add(variety.transplant_week_start_id)
            if variety.transplant_week_end_id:
                week_ids.add(variety.transplant_week_end_id)
            if variety.prune_week_start_id:
                week_ids.add(variety.prune_week_start_id)
            if variety.prune_week_end_id:
                week_ids.add(variety.prune_week_end_id)
            if variety.feed_week_start_id:
                week_ids.add(variety.feed_week_start_id)

        with log_timing("db_get_week_numbers", request_id=self.request_id):
            stmt = select(Week.week_id, Week.week_number).where(
                Week.week_id.in_(week_ids)
            )
            result = await self.db.execute(stmt)
            return {week_id: week_number for week_id, week_number in result.all()}

    async def _is_week_in_range_by_number(
        self,
        current_week_number: int,
        start_week_id: uuid.UUID,
        end_week_id: uuid.UUID,
        week_id_to_number: Dict[uuid.UUID, int],
    ) -> bool:
        """
        Check if current week is within the range (inclusive).
        Handles year wrap-around (e.g., week 50 to week 5).
        """
        start_week_number = week_id_to_number.get(start_week_id)
        end_week_number = week_id_to_number.get(end_week_id)

        if start_week_number is None or end_week_number is None:
            return False

        # Normal case: start before end (e.g., week 10 to week 30)
        if start_week_number <= end_week_number:
            return start_week_number <= current_week_number <= end_week_number

        # Wrap-around case: end before start (e.g., week 50 to week 5)
        # Current week is in range if >= start OR <= end
        return (
            current_week_number >= start_week_number
            or current_week_number <= end_week_number
        )

    async def _should_compost_variety(
        self,
        variety: Variety,
        current_week_number: int,
        week_id_to_number: Dict[uuid.UUID, int],
    ) -> bool:
        """
        Determine if a variety should be composted based on lifecycle.

        Annual: Compost after harvest_week_end
        Biennial: Compost after 2 years (104 weeks) from sow_week_start
        Perennial: Compost after productivity_years from sow_week_start
        """
        if not variety.lifecycle:
            return False

        lifecycle = self._to_lifecycle_type(variety.lifecycle.lifecycle_name)
        harvest_end_week = week_id_to_number.get(variety.harvest_week_end_id)

        if harvest_end_week is None:
            return False

        if lifecycle == LifecycleType.ANNUAL:
            # Annuals: compost immediately after harvest ends
            # Handle wrap-around
            if harvest_end_week < current_week_number:
                # Normal case: harvest ended earlier in year
                return current_week_number > harvest_end_week
            else:
                # Could be in next year after harvest
                return False

        elif lifecycle in (LifecycleType.BIENNIAL, LifecycleType.PERENNIAL):
            return False

        return False

    def _get_current_week_number(self) -> int:
        """Get the current week number based on today's date."""
        # Calculate current week number (1-52) based on ISO week date
        today = datetime.now()
        iso_calendar = today.isocalendar()
        return iso_calendar[1]  # Week number

    def _to_lifecycle_type(self, value: Union[LifecycleType, str]) -> LifecycleType:
        """Coerce a string or enum to LifecycleType safely.

        Accepts lowercase/uppercase strings; defaults to ANNUAL if unknown.
        """
        if isinstance(value, LifecycleType):
            return value
        try:
            # Normalize to lowercase values used by the enum
            return LifecycleType(value.lower())
        except Exception:
            return LifecycleType.ANNUAL

    def _create_empty_todo_response(self, week: Week) -> Dict[str, Any]:
        """Create an empty todo response when user has no active varieties."""
        return {
            "week_id": week.week_id,
            "week_number": week.week_number,
            "week_start_date": week.week_start_date,
            "week_end_date": week.week_end_date,
            "weekly_tasks": {
                "sow_tasks": [],
                "transplant_tasks": [],
                "harvest_tasks": [],
                "prune_tasks": [],
                "compost_tasks": [],
            },
            "daily_tasks": {},
        }

    def _parse_uuid(self, value: str, field: str) -> uuid.UUID:
        """Parse and validate UUID string."""
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError) as exc:
            logger.debug(
                "Invalid UUID format received",
                field=field,
                value=value,
                request_id=self.request_id,
            )
            raise BusinessLogicError(
                message=f"Invalid {field} format: {value}",
                status_code=400,
            ) from exc
