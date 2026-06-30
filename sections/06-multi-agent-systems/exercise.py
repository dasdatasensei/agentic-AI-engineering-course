"""Section 6 exercise — Project 3: Three-agent team.

Build a supervisor agent that coordinates three specialists — web
intelligence, knowledge retrieval, synthesis — dispatched in parallel via
asyncio.gather. Implement the resilient concurrency pattern from Lecture
6.5 so one failing specialist doesn't take down the whole batch.
"""

from __future__ import annotations

import asyncio
import logging

from era_platform.agents.base import AgentError, BaseAgent
from era_platform.state.schema import ResearchState

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class WebIntelligenceAgent(BaseAgent):
    """TODO: implement — wraps Tavily search + dedup (builds on Section 4.5)."""

    async def run(self, **kwargs: object) -> object:
        raise NotImplementedError

    def validate_output(self, output: object) -> bool:
        raise NotImplementedError


class RAGRetrievalAgent(BaseAgent):
    """TODO: implement — wraps your Section 3 retrieval pipeline."""

    async def run(self, **kwargs: object) -> object:
        raise NotImplementedError

    def validate_output(self, output: object) -> bool:
        raise NotImplementedError


async def dispatch_specialists(state: ResearchState, agents: list[BaseAgent]) -> ResearchState:
    """Run all specialist agents in parallel, handling partial failures
    per the Lecture 6.5 pattern: return_exceptions=True, then separate
    successes from failures rather than letting one failure cancel the batch.

    TODO: implement
    """
    results = await asyncio.gather(
        *(agent.safe_run(state=state) for agent in agents),
        return_exceptions=True,
    )

    for result in results:
        if isinstance(result, AgentError):
            logger.warning("Specialist failed: %s", result)
            state.errors.append(str(result))
        # TODO: merge successful results into state.evidence

    return state


if __name__ == "__main__":
    state = ResearchState(run_id="test-run", brief="Three-agent team smoke test")
    agents: list[BaseAgent] = [WebIntelligenceAgent("web_intel"), RAGRetrievalAgent("rag_retrieval")]
    asyncio.run(dispatch_specialists(state, agents))
