"""Web search tool — Tavily primary with a DuckDuckGo fallback (lecture 4.5).

Created: 2026-07-02
Last updated: 2026-07-02

Lecture 4.5 pairs a primary search provider (Tavily — a paid-but-free-tier API
built for agents) with a keyless fallback (DuckDuckGo) so the tool keeps working
when the Tavily quota (1,000 credits/month) is exhausted. That graceful
degradation is a first-class requirement in this course, not an afterthought:
"free-tier ceilings are real limits" (CLAUDE.md), so a research agent that dies
the moment Tavily returns 429 is not production-shaped.

The tool depends on a tiny :class:`SearchProvider` protocol rather than the SDKs
directly — the same "smallest honest interface" discipline as
:class:`~era_platform.rag.embeddings.Embedder`. Concrete providers
(:class:`TavilyProvider`, :class:`DuckDuckGoProvider`) import their SDK lazily so
this module stays importable, and the package type-checkable, without the search
extras installed; tests inject fake providers and never touch the network.
"""

from __future__ import annotations

import logging
import os
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from era_platform.agents.tools.base import Tool, ToolError

logger = logging.getLogger(__name__)

DEFAULT_MAX_RESULTS = 5


class SearchHit(BaseModel):
    """A single web result: where it came from and a snippet to reason over."""

    title: str = Field(default="", description="The result's title, if the provider gives one.")
    url: str = Field(default="", description="The source URL.")
    content: str = Field(description="A snippet or summary of the page content.")


@runtime_checkable
class SearchProvider(Protocol):
    """The minimal interface the web-search tool needs from a backend.

    One method: run a query and return ranked :class:`SearchHit`s. Tavily,
    DuckDuckGo, or a deterministic fake in tests all satisfy it. A provider should
    raise on failure (empty results are *not* a failure — that is a valid "found
    nothing"); the tool turns a raised error into a fallback or a
    :class:`~era_platform.agents.tools.base.ToolError`.
    """

    def search(self, query: str, *, max_results: int) -> list[SearchHit]:
        """Return up to ``max_results`` hits for ``query`` (may be empty)."""
        ...


class TavilyProvider:
    """A :class:`SearchProvider` backed by Tavily (the course's primary search).

    Wraps ``tavily.TavilyClient``. The import is lazy (inside ``__init__``) so
    importing this module never requires ``tavily-python`` to be installed — only
    constructing a :class:`TavilyProvider` does.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Build a Tavily-backed provider.

        Args:
            api_key: Tavily API key. Defaults to ``TAVILY_API_KEY`` from the
                environment.

        Raises:
            ToolError: If no API key can be resolved.
        """
        from tavily import TavilyClient

        resolved_key = api_key or os.environ.get("TAVILY_API_KEY")
        if not resolved_key:
            raise ToolError("TAVILY_API_KEY is not set; cannot construct a Tavily provider")
        self._client = TavilyClient(api_key=resolved_key)

    def search(self, query: str, *, max_results: int) -> list[SearchHit]:
        """Run a Tavily search. See :meth:`SearchProvider.search`."""
        response = self._client.search(query=query, max_results=max_results)
        results = response.get("results", []) if isinstance(response, dict) else []
        return [
            SearchHit(
                title=str(item.get("title", "")),
                url=str(item.get("url", "")),
                content=str(item.get("content", "")),
            )
            for item in results
        ]


class DuckDuckGoProvider:
    """A keyless :class:`SearchProvider` fallback backed by ``duckduckgo-search``.

    Used when Tavily has no key or its quota is exhausted. Import is lazy for the
    same reason as :class:`TavilyProvider`.
    """

    def __init__(self) -> None:
        from duckduckgo_search import DDGS

        self._ddgs_factory = DDGS

    def search(self, query: str, *, max_results: int) -> list[SearchHit]:
        """Run a DuckDuckGo search. See :meth:`SearchProvider.search`."""
        with self._ddgs_factory() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [
            SearchHit(
                title=str(item.get("title", "")),
                url=str(item.get("href", "")),
                content=str(item.get("body", "")),
            )
            for item in results
        ]


class WebSearchTool(Tool):
    """Search the web, preferring ``primary`` and degrading to ``fallback``.

    On a primary failure (quota, network, missing key) it logs a WARNING and
    retries the query against the fallback — the lecture-4.5 pattern. Only when
    *both* fail (or neither is configured) does it raise
    :class:`~era_platform.agents.tools.base.ToolError`, which the agent then turns
    into a recoverable observation.
    """

    def __init__(
        self,
        primary: SearchProvider | None = None,
        fallback: SearchProvider | None = None,
        *,
        max_results: int = DEFAULT_MAX_RESULTS,
    ) -> None:
        """Build the web-search tool.

        Args:
            primary: Preferred provider (Tavily in the course default). May be
                ``None`` when no key is available, in which case the fallback is
                used directly.
            fallback: Keyless provider tried when the primary fails or is absent.
            max_results: Default number of hits to request per query.

        Raises:
            ValueError: If neither a primary nor a fallback provider is given.
        """
        if primary is None and fallback is None:
            raise ValueError("WebSearchTool needs at least one of primary/fallback")
        super().__init__(
            name="web_search",
            description="Search the web for current, external information.",
            parameters={"query": "the search query as a natural-language string"},
        )
        self._primary = primary
        self._fallback = fallback
        self._max_results = max_results

    def run(self, **kwargs: object) -> str:
        """Search for ``query`` and return the ranked hits as text.

        Raises:
            ToolError: If ``query`` is missing/blank or every configured provider
                fails.
        """
        query = kwargs.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ToolError("web_search requires a non-empty 'query' string")

        hits, provider_used = self._search_with_fallback(query.strip())
        if not hits:
            return f"No web results found for {query!r}."
        self._logger.info("web_search via %s returned %d hits", provider_used, len(hits))
        return self._format(hits)

    def _search_with_fallback(self, query: str) -> tuple[list[SearchHit], str]:
        errors: list[str] = []
        if self._primary is not None:
            try:
                return self._primary.search(query, max_results=self._max_results), "primary"
            except Exception as exc:  # noqa: BLE001 — degrade to fallback on any primary failure
                errors.append(f"primary: {exc}")
                self._logger.warning(
                    "primary web search failed, falling back to secondary: %s", exc
                )
        if self._fallback is not None:
            try:
                return self._fallback.search(query, max_results=self._max_results), "fallback"
            except Exception as exc:  # noqa: BLE001 — both failing is the only hard error
                errors.append(f"fallback: {exc}")
                self._logger.error("fallback web search also failed: %s", exc)
        raise ToolError(f"all web search providers failed ({'; '.join(errors)})")

    @staticmethod
    def _format(hits: list[SearchHit]) -> str:
        lines = [
            f"[{i}] {hit.title or hit.url or 'result'}\n{hit.content}".strip()
            for i, hit in enumerate(hits, start=1)
        ]
        return "\n\n".join(lines)
