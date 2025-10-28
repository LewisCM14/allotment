"""
Enums for database models
- Provides type-safe enums for database fields
"""

from enum import Enum


class LifecycleType(str, Enum):
    """
    Enum for plant lifecycle types.

    - ANNUAL: Plants that complete their lifecycle in one growing season
    - BIENNIAL: Plants that complete their lifecycle in two growing seasons
    - PERENNIAL: Plants that live for multiple years
    - SHORT_LIVED_PERENNIAL: Perennials with a notably shorter productive lifespan
    """

    ANNUAL = "annual"
    BIENNIAL = "biennial"
    PERENNIAL = "perennial"
    SHORT_LIVED_PERENNIAL = "short-lived perennial"
