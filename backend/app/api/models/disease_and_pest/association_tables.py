from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

from app.api.core.database import Base

# Pest Treatment
pest_treatment = Table(
    "pest_treatment",
    Base.metadata,
    Column(
        "pest_id",
        UUID(as_uuid=True),
        ForeignKey("pest.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "intervention_id",
        UUID(as_uuid=True),
        ForeignKey("intervention.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Pest Prevention
pest_prevention = Table(
    "pest_prevention",
    Base.metadata,
    Column(
        "pest_id",
        UUID(as_uuid=True),
        ForeignKey("pest.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "intervention_id",
        UUID(as_uuid=True),
        ForeignKey("intervention.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Disease Treatment
disease_treatment = Table(
    "disease_treatment",
    Base.metadata,
    Column(
        "disease_id",
        UUID(as_uuid=True),
        ForeignKey("disease.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "intervention_id",
        UUID(as_uuid=True),
        ForeignKey("intervention.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Disease Prevention
disease_prevention = Table(
    "disease_prevention",
    Base.metadata,
    Column(
        "disease_id",
        UUID(as_uuid=True),
        ForeignKey("disease.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "intervention_id",
        UUID(as_uuid=True),
        ForeignKey("intervention.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Disease Symptom
disease_symptom = Table(
    "disease_symptom",
    Base.metadata,
    Column(
        "disease_id",
        UUID(as_uuid=True),
        ForeignKey("disease.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "symptom_id",
        UUID(as_uuid=True),
        ForeignKey("symptom.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Family Pest
family_pest = Table(
    "family_pest",
    Base.metadata,
    Column(
        "family_id",
        UUID(as_uuid=True),
        ForeignKey("family.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "pest_id",
        UUID(as_uuid=True),
        ForeignKey("pest.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Family Disease
family_disease = Table(
    "family_disease",
    Base.metadata,
    Column(
        "family_id",
        UUID(as_uuid=True),
        ForeignKey("family.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "disease_id",
        UUID(as_uuid=True),
        ForeignKey("disease.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
