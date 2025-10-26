"""
Integration tests for weekly todo endpoints.
"""

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.core.config import settings

PREFIX = settings.API_PREFIX


class TestWeeklyTodoIntegration:
    @pytest.mark.asyncio
    async def test_get_weekly_todo_success(
        self, client: TestClient, register_user
    ) -> None:
        """Get weekly todo successfully."""

        headers = await register_user("todo_user")

        # Mock the response data
        mock_todo_data = {
            "week_id": str(uuid.uuid4()),
            "week_number": 20,
            "week_start_date": "05/13",
            "week_end_date": "05/19",
            "weekly_tasks": {
                "sow_tasks": [
                    {
                        "variety_id": str(uuid.uuid4()),
                        "variety_name": "tomato",
                        "family_name": "nightshade",
                    }
                ],
                "transplant_tasks": [],
                "harvest_tasks": [],
                "prune_tasks": [],
                "compost_tasks": [],
            },
            "daily_tasks": {
                1: {
                    "day_id": str(uuid.uuid4()),
                    "day_number": 1,
                    "day_name": "Mon",
                    "feed_tasks": [],
                    "water_tasks": [],
                }
            },
        }

        with patch(
            "app.api.services.todo.weekly_todo.WeeklyTodoUnitOfWork.get_weekly_todo",
            return_value=mock_todo_data,
        ):
            response = await client.get(f"{PREFIX}/todos/weekly", headers=headers)

        assert response.status_code == 200
        payload = response.json()
        assert payload["week_number"] == 20
        assert "weekly_tasks" in payload
        assert "daily_tasks" in payload
        assert len(payload["weekly_tasks"]["sow_tasks"]) == 1

    @pytest.mark.asyncio
    async def test_get_weekly_todo_specific_week(
        self, client: TestClient, register_user
    ) -> None:
        """Get weekly todo for a specific week number."""

        headers = await register_user("todo_user_specific")

        mock_todo_data = {
            "week_id": str(uuid.uuid4()),
            "week_number": 30,
            "week_start_date": "07/22",
            "week_end_date": "07/28",
            "weekly_tasks": {
                "sow_tasks": [],
                "transplant_tasks": [],
                "harvest_tasks": [
                    {
                        "variety_id": str(uuid.uuid4()),
                        "variety_name": "cucumber",
                        "family_name": "cucurbit",
                    }
                ],
                "prune_tasks": [],
                "compost_tasks": [],
            },
            "daily_tasks": {},
        }

        with patch(
            "app.api.services.todo.weekly_todo.WeeklyTodoUnitOfWork.get_weekly_todo",
            return_value=mock_todo_data,
        ):
            response = await client.get(
                f"{PREFIX}/todos/weekly?week_number=30", headers=headers
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["week_number"] == 30
        assert len(payload["weekly_tasks"]["harvest_tasks"]) == 1

    @pytest.mark.asyncio
    async def test_get_weekly_todo_invalid_week_number(
        self, client: TestClient, register_user
    ) -> None:
        """Invalid week number should trigger validation error."""

        headers = await register_user("todo_user_invalid")

        # Week number too high
        response = await client.get(
            f"{PREFIX}/todos/weekly?week_number=53", headers=headers
        )
        assert response.status_code == 422

        # Week number too low
        response = await client.get(
            f"{PREFIX}/todos/weekly?week_number=0", headers=headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_weekly_todo_unauthorized(self, client: TestClient) -> None:
        """Ensure getting weekly todo without a token is rejected."""

        response = await client.get(f"{PREFIX}/todos/weekly")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_weekly_todo_no_active_varieties(
        self, client: TestClient, register_user
    ) -> None:
        """Get weekly todo when user has no active varieties."""

        headers = await register_user("todo_user_empty")

        mock_todo_data = {
            "week_id": str(uuid.uuid4()),
            "week_number": 15,
            "week_start_date": "04/08",
            "week_end_date": "04/14",
            "weekly_tasks": {
                "sow_tasks": [],
                "transplant_tasks": [],
                "harvest_tasks": [],
                "prune_tasks": [],
                "compost_tasks": [],
            },
            "daily_tasks": {},
        }

        with patch(
            "app.api.services.todo.weekly_todo.WeeklyTodoUnitOfWork.get_weekly_todo",
            return_value=mock_todo_data,
        ):
            response = await client.get(f"{PREFIX}/todos/weekly", headers=headers)

        assert response.status_code == 200
        payload = response.json()
        assert payload["week_number"] == 15
        assert len(payload["weekly_tasks"]["sow_tasks"]) == 0
        assert len(payload["daily_tasks"]) == 0

    @pytest.mark.asyncio
    async def test_get_weekly_todo_with_daily_tasks(
        self, client: TestClient, register_user
    ) -> None:
        """Get weekly todo with complete daily tasks."""

        headers = await register_user("todo_user_daily")

        mock_todo_data = {
            "week_id": str(uuid.uuid4()),
            "week_number": 25,
            "week_start_date": "06/17",
            "week_end_date": "06/23",
            "weekly_tasks": {
                "sow_tasks": [],
                "transplant_tasks": [],
                "harvest_tasks": [],
                "prune_tasks": [],
                "compost_tasks": [],
            },
            "daily_tasks": {
                1: {
                    "day_id": str(uuid.uuid4()),
                    "day_number": 1,
                    "day_name": "Mon",
                    "feed_tasks": [
                        {
                            "feed_id": str(uuid.uuid4()),
                            "feed_name": "tomato feed",
                            "varieties": [
                                {
                                    "variety_id": str(uuid.uuid4()),
                                    "variety_name": "roma",
                                    "family_name": "nightshade",
                                }
                            ],
                        }
                    ],
                    "water_tasks": [
                        {
                            "variety_id": str(uuid.uuid4()),
                            "variety_name": "lettuce",
                            "family_name": "asteraceae",
                        }
                    ],
                },
                3: {
                    "day_id": str(uuid.uuid4()),
                    "day_number": 3,
                    "day_name": "Wed",
                    "feed_tasks": [],
                    "water_tasks": [],
                },
            },
        }

        with patch(
            "app.api.services.todo.weekly_todo.WeeklyTodoUnitOfWork.get_weekly_todo",
            return_value=mock_todo_data,
        ):
            response = await client.get(f"{PREFIX}/todos/weekly", headers=headers)

        assert response.status_code == 200
        payload = response.json()
        assert "1" in payload["daily_tasks"]
        assert len(payload["daily_tasks"]["1"]["feed_tasks"]) == 1
        assert len(payload["daily_tasks"]["1"]["water_tasks"]) == 1
        assert (
            payload["daily_tasks"]["1"]["feed_tasks"][0]["feed_name"] == "tomato feed"
        )
