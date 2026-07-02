"""Knowledge-search tool — wraps Section 3's retrieval as the agent's third tool.

Created: 2026-07-02
Last updated: 2026-07-02

This is the tool that makes Exercise 4.E a *research* agent rather than three
disconnected demos: it gives the ReAct loop access to the learner's own indexed
document collection by wrapping the
:class:`~era_platform.rag.knowledge_agent.KnowledgeRetrievalAgent` built in
Project 1 (3.P). No new retrieval concepts are introduced here — 4.E reuses
Section 3's work, exactly the "extend, don't fork" rule in CLAUDE.md — and it
sets up Project 2 (5.P), where the same web-search + RAG pairing is lifted into a
LangGraph ``StateGraph``.

Because it depends on the *already-injected* ``KnowledgeRetrievalAgent`` (itself
built from the ``Embedder`` protocol and a ChromaDB collection), tests wrap a fake
agent and never touch a real embedder, network, or on-disk store.
"""

from __future__ import annotations

import logging

from era_platform.agents.tools.base import Tool, ToolError
from era_platform.rag.knowledge_agent import KnowledgeQuery, KnowledgeRetrievalAgent

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 4


class KnowledgeSearchTool(Tool):
    """Retrieve passages from the ERA knowledge base for the ReAct agent.

    Delegates to an injected :class:`KnowledgeRetrievalAgent`, formatting its
    :class:`~era_platform.rag.retrieval.RetrievedChunk` hits (with their source
    names, so the agent can cite them) into the observation string.
    """

    def __init__(
        self,
        knowledge_agent: KnowledgeRetrievalAgent,
        *,
        top_k: int = DEFAULT_TOP_K,
        hybrid: bool = True,
    ) -> None:
        """Build the knowledge-search tool.

        Args:
            knowledge_agent: The 3.P retrieval layer to query.
            top_k: Maximum passages to return per query. Must be positive.
            hybrid: Whether to fuse dense + BM25 keyword retrieval (3.P's default).

        Raises:
            ValueError: If ``top_k`` is not positive.
        """
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        super().__init__(
            name="knowledge_search",
            description=(
                "Search the local knowledge base of ingested documents for "
                "relevant passages. Use this before the web for anything the "
                "user's own documents may cover."
            ),
            parameters={"query": "the natural-language question to look up in the documents"},
        )
        self._agent = knowledge_agent
        self._top_k = top_k
        self._hybrid = hybrid

    def run(self, **kwargs: object) -> str:
        """Retrieve passages for ``query`` and return them (with sources) as text.

        Raises:
            ToolError: If ``query`` is missing/blank or retrieval fails.
        """
        query = kwargs.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ToolError("knowledge_search requires a non-empty 'query' string")

        try:
            hits = self._agent.retrieve(
                KnowledgeQuery(question=query.strip(), top_k=self._top_k, hybrid=self._hybrid)
            )
        except Exception as exc:  # noqa: BLE001 — normalise retrieval failures at the boundary
            self._logger.error("knowledge_search failed for %r: %s", query, exc)
            raise ToolError(f"knowledge base retrieval failed: {exc}") from exc

        if not hits:
            return f"No relevant passages found in the knowledge base for {query!r}."

        self._logger.info("knowledge_search returned %d passages", len(hits))
        lines = [
            f"[{i}] (source: {hit.metadata.get('source', 'unknown')})\n{hit.text}"
            for i, hit in enumerate(hits, start=1)
        ]
        return "\n\n".join(lines)
