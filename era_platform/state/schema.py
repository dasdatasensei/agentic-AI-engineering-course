"""The ResearchState schema — the single typed contract every agent in the
ERA Platform reads from and writes to.

Introduced in Section 5 (LangGraph) as the state object passed between
StateGraph nodes. Extended in Section 6 (multi-agent evidence aggregation)
and Section 12 (the full five-agent capstone).
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    """Lifecycle status of a research run."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETE = "complete"
    FAILED = "failed"


class Evidence(BaseModel):
    """A single piece of evidence gathered by any agent, with enough
    provenance to support citation in the final synthesized report.
    """

    source_id: str
    source_type: str  # "web", "document", "computation"
    content: str
    credibility_score: float = Field(ge=0.0, le=1.0, default=0.5)
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def _merge_evidence(left: list[Evidence], right: list[Evidence]) -> list[Evidence]:
    """Reducer for the `evidence` field — appends new evidence from parallel
    agent nodes rather than overwriting, which is what makes Section 6's
    parallel dispatch pattern safe to use with this schema.
    """
    return left + right


class ResearchState(BaseModel):
    """The typed state object passed through every node of the orchestrator's
    StateGraph. No agent in this system passes unstructured strings between
    each other — everything goes through this contract.
    """

    run_id: str
    brief: str
    status: RunStatus = RunStatus.PENDING

    evidence: Annotated[list[Evidence], _merge_evidence] = Field(default_factory=list)

    draft_report: str | None = None
    final_report: str | None = None

    errors: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"frozen": False}
