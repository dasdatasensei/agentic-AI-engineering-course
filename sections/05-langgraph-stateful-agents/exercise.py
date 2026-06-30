"""Section 5 exercise — Project 2: Convert your Section 4 agent into a
LangGraph StateGraph.

Take the plain ReAct loop you wrote in Section 4 and re-express it as nodes
and edges on a typed StateGraph, using the ResearchState schema from
era_platform/state/schema.py. Add conditional routing, checkpoint
persistence, and a human-in-the-loop review gate before the final answer
is returned.
"""

from __future__ import annotations

import logging

from era_platform.state.schema import ResearchState

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# TODO: import langgraph.graph.StateGraph once you reach Lecture 5.2


def parse_brief_node(state: ResearchState) -> ResearchState:
    """First node in the graph — validates and normalizes the incoming
    research brief before any agent work begins.

    TODO: implement (Lecture 5.2, 5.3)
    """
    raise NotImplementedError


def route_after_parse(state: ResearchState) -> str:
    """Conditional routing function — decides which node runs next based
    on the current state. (Lecture 5.4)

    TODO: implement
    """
    raise NotImplementedError


def build_graph() -> object:
    """Assemble the full StateGraph: parse_brief -> route -> agent nodes ->
    synthesis -> human-in-the-loop gate -> finalize.

    TODO: implement using langgraph.graph.StateGraph(ResearchState).
    Add checkpoint persistence (Lecture 5.5) and the interrupt_before
    pattern for the HITL gate (Lecture 5.7).
    """
    raise NotImplementedError


if __name__ == "__main__":
    graph = build_graph()
    logger.info("Graph built: %s", graph)
