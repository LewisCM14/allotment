"""
Weekly Todo Unit of Work
- Coordinates retrieval of weekly and daily tasks for a user's active varieties.
- Aggregates data from Week, Day, Variety, UserActiveVariety, Feed, and Frequency tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from types import TracebackType
from typing import Any, Dict, List, Optional, Type

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

        current_week_number = current_week.week_number

        def add_task_if_in_range(
            task_key: str,
            start_id: Optional[uuid.UUID],
            end_id: Optional[uuid.UUID],
            info: Dict[str, Any],
        ) -> None:
            """Append variety_info to tasks[task_key] if current week is in range.

            Requires both start and end week IDs and delegates range logic to
            _is_week_in_range_by_number.
            """
            if not (start_id and end_id):
                return
            # Narrow types for mypy
            sid, eid = start_id, end_id
            assert sid is not None and eid is not None
            if self._is_week_in_range_by_number(
                current_week_number, sid, eid, week_id_to_number
            ):
                tasks[task_key].append(info)

        for variety in active_varieties:
            variety_info = {
                "variety_id": variety.variety_id,
                "variety_name": variety.variety_name,
                "family_name": variety.family.family_name if variety.family else "",
            }

            # Weekly windows
            add_task_if_in_range(
                "sow_tasks",
                variety.sow_week_start_id,
                variety.sow_week_end_id,
                variety_info,
            )
            add_task_if_in_range(
                "transplant_tasks",
                variety.transplant_week_start_id,
                variety.transplant_week_end_id,
                variety_info,
            )
            add_task_if_in_range(
                "harvest_tasks",
                variety.harvest_week_start_id,
                variety.harvest_week_end_id,
                variety_info,
            )
            add_task_if_in_range(
                "prune_tasks",
                variety.prune_week_start_id,
                variety.prune_week_end_id,
                variety_info,
            )

            # Check if variety should be composted based on lifecycle
            if self._should_compost_variety(
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

    def _get_lifecycle_name(self, variety: Variety) -> LifecycleType | str:
        """Extract lifecycle name or default to ANNUAL."""
        return (
            variety.lifecycle.lifecycle_name
            if variety.lifecycle
            else LifecycleType.ANNUAL
        )

    def _create_variety_info(self, variety: Variety) -> Dict[str, Any]:
        """Build standard variety info dict."""
        return {
            "variety_id": variety.variety_id,
            "variety_name": variety.variety_name,
            "family_name": variety.family.family_name if variety.family else "",
        }

    async def _build_feed_tasks_for_day(
        self,
        active_varieties: List[Variety],
        day_id: uuid.UUID,
        week_number: int,
        user_feed_days: Dict[uuid.UUID, uuid.UUID],
    ) -> List[Dict[str, Any]]:
        """Build feeding tasks for a specific day, grouped by feed type."""
        feed_groups: Dict[uuid.UUID, Dict[str, Any]] = {}

        def ensure_group(fid: uuid.UUID, feed_name: str) -> Dict[str, Any]:
            if fid not in feed_groups:
                feed_groups[fid] = {
                    "feed_id": fid,
                    "feed_name": feed_name,
                    "varieties": [],
                }
            return feed_groups[fid]

        for variety in active_varieties:
            fid = variety.feed_id
            fws = variety.feed_week_start_id
            ffid = variety.feed_frequency_id
            if not (fid and fws and ffid):
                continue
            if user_feed_days.get(fid) != day_id:
                continue

            in_period = await self._is_week_in_feeding_period(
                week_number,
                fws,
                ffid,
                variety.harvest_week_end_id,
                self._get_lifecycle_name(variety),
            )
            if not in_period:
                continue

            feed_name = variety.feed.feed_name if variety.feed else ""
            group = ensure_group(fid, feed_name)
            group["varieties"].append(self._create_variety_info(variety))

        return list(feed_groups.values())

    async def _fetch_missing_week_numbers(
        self,
        sid: uuid.UUID,
        hid: uuid.UUID,
        start_num: Optional[int],
        end_num: Optional[int],
        week_id_to_number: Dict[uuid.UUID, int],
    ) -> tuple[Optional[int], Optional[int]]:
        """Fetch missing week numbers from database and update cache."""
        missing = [
            wid for wid, num in [(sid, start_num), (hid, end_num)] if num is None
        ]
        if missing:
            stmt = select(Week.week_id, Week.week_number).where(
                Week.week_id.in_(missing)
            )
            result = await self.db.execute(stmt)
            for wid, wnum in result.all():
                if wid not in week_id_to_number:
                    week_id_to_number[wid] = wnum
            start_num = week_id_to_number.get(sid)
            end_num = week_id_to_number.get(hid)
        return start_num, end_num

    async def _get_annual_bounds(
        self, variety: Variety, week_id_to_number: Dict[uuid.UUID, int]
    ) -> Optional[tuple[int, int]]:
        """Return (start, end) week numbers for annual varieties, fetching missing values if needed."""
        if not variety.lifecycle:
            return None

        if (
            self._to_lifecycle_type(variety.lifecycle.lifecycle_name)
            != LifecycleType.ANNUAL
        ):
            return None

        sid = variety.sow_week_start_id
        hid = variety.harvest_week_end_id

        if not sid or not hid:
            return None

        start_num = week_id_to_number.get(sid)
        end_num = week_id_to_number.get(hid)

        if start_num is None or end_num is None:
            start_num, end_num = await self._fetch_missing_week_numbers(
                sid, hid, start_num, end_num, week_id_to_number
            )

        if start_num is None or end_num is None:
            return None

        return start_num, end_num

    def _is_in_season(
        self, current_week: int, bounds: Optional[tuple[int, int]]
    ) -> bool:
        """Check if current week is within the season bounds (handles year wrap-around)."""
        if bounds is None:
            return True

        start, end = bounds
        if start <= end:
            return start <= current_week <= end

        return current_week >= start or current_week <= end

    def _should_water_today(self, variety: Variety, day_id: uuid.UUID) -> bool:
        """Check if variety should be watered on the given day."""
        if not (variety.water_frequency and variety.water_frequency.default_days):
            return False

        return any(d.day_id == day_id for d in variety.water_frequency.default_days)

    async def _build_water_tasks_for_day(
        self,
        active_varieties: List[Variety],
        day_id: uuid.UUID,
        week_number: int,
        week_id_to_number: Dict[uuid.UUID, int],
    ) -> List[Dict[str, Any]]:
        """Build watering tasks for a specific day using frequency default days."""
        water_tasks: List[Dict[str, Any]] = []

        for variety in active_varieties:
            bounds = await self._get_annual_bounds(variety, week_id_to_number)
            if bounds is not None and not self._is_in_season(week_number, bounds):
                continue

            if not self._should_water_today(variety, day_id):
                continue

            water_tasks.append(self._create_variety_info(variety))

        return water_tasks

    def _calculate_weeks_between_feeds(self, occurrences: int) -> int:
        """Calculate weeks between feeds based on yearly occurrences."""
        if occurrences >= 52:
            return 1
        return max(1, int(round(52.0 / occurrences)))

    def _check_week_in_lifecycle_window(
        self, wn: int, start: int, harvest_end: Optional[int], lifecycle: LifecycleType
    ) -> int:
        """Return adjusted week number if within lifecycle period; -1 if outside."""
        if lifecycle in (LifecycleType.ANNUAL, LifecycleType.SHORT_LIVED_PERENNIAL):
            if harvest_end is None:
                return -1
            if start <= harvest_end:
                return wn if (start <= wn <= harvest_end) else -1
            # wrap-around
            return wn if (wn >= start or wn <= harvest_end) else -1
        # perennials/biennials
        if wn < start:
            wn += 52
        return wn

    async def _is_week_in_feeding_period(
        self,
        week_number: int,
        feed_week_start_id: uuid.UUID,
        feed_frequency_id: uuid.UUID,
        harvest_week_end_id: uuid.UUID,
        lifecycle_name: LifecycleType | str,
    ) -> bool:
        """
            Check if the given week is within the feeding period.

        For annuals and short-lived perennials: Feed from feed_week_start until harvest_week_end.
        For perennials/biennials: Feed from feed_week_start onwards (continues across years).

            Frequency determines HOW OFTEN to feed within the period.
        """
        with log_timing("db_check_feeding_period", request_id=self.request_id):
            # Get numeric start week
            stmt = select(Week.week_number).where(Week.week_id == feed_week_start_id)
            result = await self.db.execute(stmt)
            start_week_number = result.scalar_one_or_none()
            if start_week_number is None:
                return False

            lifecycle = self._to_lifecycle_type(lifecycle_name)

            # Fetch harvest end week if needed for lifecycle window
            harvest_end_week: Optional[int] = None
            if lifecycle in (LifecycleType.ANNUAL, LifecycleType.SHORT_LIVED_PERENNIAL):
                harvest_stmt = select(Week.week_number).where(
                    Week.week_id == harvest_week_end_id
                )
                harvest_result = await self.db.execute(harvest_stmt)
                harvest_end_week = harvest_result.scalar_one_or_none()

            # Get frequency
            freq_stmt = select(Frequency).where(
                Frequency.frequency_id == feed_frequency_id
            )
            freq_result = await self.db.execute(freq_stmt)
            frequency = freq_result.scalar_one_or_none()
            if frequency is None:
                return False

            # Check if week is within lifecycle window
            adjusted_week = self._check_week_in_lifecycle_window(
                week_number, start_week_number, harvest_end_week, lifecycle
            )
            if adjusted_week < 0:
                return False

            # Check feeding cadence
            occurrences = max(0, int(frequency.frequency_days_per_year))
            if occurrences <= 0:
                return False
            weeks_between = self._calculate_weeks_between_feeds(occurrences)

            # Normalize delta in [0, 51]
            delta = adjusted_week - start_week_number
            if delta < 0:
                delta += 52
            return delta % weeks_between == 0

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
            return {row[0]: row[1] for row in result.all()}

    def _is_week_in_range_by_number(
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

    def _should_compost_variety(
        self,
        variety: Variety,
        current_week_number: int,
        week_id_to_number: Dict[uuid.UUID, int],
    ) -> bool:
        """
        Determine if a variety should be composted based on lifecycle.

        Annual: Compost between the last harvest week and the next sow start week.
        That is, outside the active season defined by [sow_week_start .. harvest_week_end]
        (inclusive), correctly handling year wrap-around.
        Biennial: Compost after 2 years (104 weeks) from sow_week_start
        Perennial: Compost after productivity_years from sow_week_start
        """
        if not variety.lifecycle:
            return False

        lifecycle = self._to_lifecycle_type(variety.lifecycle.lifecycle_name)
        sow_start_week = week_id_to_number.get(variety.sow_week_start_id)
        harvest_end_week = week_id_to_number.get(variety.harvest_week_end_id)

        if lifecycle == LifecycleType.ANNUAL:
            # Need both bounds to determine in-season vs compost window
            if sow_start_week is None or harvest_end_week is None:
                return False

            if sow_start_week <= harvest_end_week:
                # Season contained within a single year (e.g., Mar..Sep)
                # Compost only AFTER harvest end within the same year; do not
                # show compost in Jan/Feb before the season begins.
                return current_week_number > harvest_end_week
            else:
                # Season wraps year (e.g., Nov..Sep)
                # Compost strictly between harvest end and next sow start
                # (weeks > harvest_end and < sow_start), e.g., October.
                return (
                    current_week_number > harvest_end_week
                    and current_week_number < sow_start_week
                )

        elif lifecycle in (
            LifecycleType.BIENNIAL,
            LifecycleType.PERENNIAL,
            LifecycleType.SHORT_LIVED_PERENNIAL,
        ):
            return False

        return False

    def _get_current_week_number(self) -> int:
        """Get the current week number based on today's date."""
        # Calculate current week number (1-52) based on ISO week date
        today = datetime.now()
        iso_calendar = today.isocalendar()
        return iso_calendar[1]  # Week number

    def _to_lifecycle_type(self, value: LifecycleType | str) -> LifecycleType:
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
