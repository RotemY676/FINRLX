"""Evidence narrative schemas.

Maps to design handoff: modules.jsx EvidenceCard structure.
"""
from pydantic import BaseModel


class EvidenceItem(BaseModel):
    """Single numbered evidence item."""
    order: int
    title: str
    body: str
    delta_label: str | None = None  # "+4.8%", "±0", "−0.22"
    delta_direction: str | None = None  # pos, neg, neutral, flat
    caveat: str | None = None
    source_engine: str | None = None


class EvidenceNarrativeResponse(BaseModel):
    """Evidence narrative for a recommendation."""
    recommendation_id: str
    items: list[EvidenceItem]
    caveat: str | None = None  # bottom-of-card caveat
    last_refreshed_min: int | None = None
