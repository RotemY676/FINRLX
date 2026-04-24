"""Action bar schemas for publish/defer/promote workflow.

Maps to design handoff: hero.jsx ActionBar.
"""
from pydantic import BaseModel


class ActionResult(BaseModel):
    """Result of an action bar operation."""
    action: str  # save_thesis, promote_paper, defer
    success: bool
    new_status: str
    message: str


class DeferRequest(BaseModel):
    """Request to defer a decision."""
    reason: str | None = None
    defer_until: str | None = None  # ISO datetime or relative like "tomorrow"
