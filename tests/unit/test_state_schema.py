"""Unit tests for era_platform.state.schema — also serves as the reference
example for how tests in this repo should be structured (Section 4.8,
'Testing your agent', covers this pattern in detail).
"""

from era_platform.state.schema import Evidence, ResearchState, RunStatus


def test_research_state_defaults() -> None:
    state = ResearchState(run_id="run-1", brief="Summarise Caribbean fintech trends")

    assert state.status == RunStatus.PENDING
    assert state.evidence == []
    assert state.draft_report is None
    assert state.errors == []


def test_evidence_accumulates_without_overwriting() -> None:
    state = ResearchState(run_id="run-2", brief="test")
    state.evidence.append(
        Evidence(source_id="src-1", source_type="web", content="finding one")
    )
    state.evidence.append(
        Evidence(source_id="src-2", source_type="document", content="finding two")
    )

    assert len(state.evidence) == 2
    assert state.evidence[0].source_id == "src-1"
    assert state.evidence[1].source_type == "document"


def test_credibility_score_bounds() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Evidence(source_id="src-3", source_type="web", content="x", credibility_score=1.5)
