"""Exercise 4.E — solution (runnable demo).

The reference *logic* lives in ``era_platform/agents/`` — the ``ResearchAgent``
(``research_agent.py``) and the three tools (``tools/``) are type-checked and
unit-tested there, so they are not duplicated here. This file shows how to *drive*
the agent: it wires up the three tools and runs a ReAct loop to answer a question.

Run it:

    # Fully offline (no keys): a scripted planner drives the loop; the code and
    # knowledge tools run for real locally, web search uses a canned provider.
    #   python .../exercise-4E-research-agent/solution/research_agent.py
    # (run from the repo root; the path is under sections/04-single-agents-...)

    # With GOOGLE_API_KEY set, the real Gemini model decides each step. Add
    # TAVILY_API_KEY to use Tavily for web search (DuckDuckGo is the fallback).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os

from dotenv import load_dotenv

from era_platform.agents import ResearchAgent
from era_platform.agents.tools import (
    CodeExecutionTool,
    DuckDuckGoProvider,
    KnowledgeSearchTool,
    SearchHit,
    TavilyProvider,
    WebSearchTool,
)
from era_platform.agents.tools.web_search import SearchProvider
from era_platform.rag import KnowledgeRetrievalAgent, SourceDocument, get_ephemeral_collection

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

QUESTION = "What is the ERA Platform, and what is 6 times 7?"

SAMPLE_DOCS = [
    SourceDocument(
        text=(
            "The ERA Platform is an Enterprise Research and Analysis Platform: a "
            "five-agent multi-agent research system orchestrated with LangGraph."
        ),
        metadata={"source": "era-overview.txt"},
    ),
    SourceDocument(
        text=(
            "A research agent answers questions by reasoning step by step and calling "
            "tools — web search, code execution, and knowledge retrieval — in a ReAct loop."
        ),
        metadata={"source": "research-agent.txt"},
    ),
]


class _LocalEmbedder:
    """A deterministic offline embedder used when no GOOGLE_API_KEY is set."""

    def __init__(self, dim: int = 128) -> None:
        self._dim = dim

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self._dim
        for token in text.lower().split():
            digest = hashlib.md5(token.encode("utf-8")).digest()
            vector[int.from_bytes(digest[:4], "big") % self._dim] += 1.0
        if not any(vector):
            vector[0] = 1.0
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class _GeminiLLM:
    """A thin ``LLMClient`` adapter around Gemini via langchain-google-genai."""

    def __init__(self) -> None:
        from langchain_google_genai import ChatGoogleGenerativeAI

        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        self._model = ChatGoogleGenerativeAI(model=model_name, temperature=0.0)

    def invoke(self, prompt: str) -> str:
        content = self._model.invoke(prompt).content
        return content if isinstance(content, str) else str(content)


class _ScriptedPlanner:
    """A canned ``LLMClient`` that walks a fixed ReAct plan, so the demo runs offline.

    It ignores the prompt and returns a preset JSON decision per step: search the
    knowledge base, run a calculation in the sandbox, then finish. This is exactly
    what a *real* model would emit — the point of the offline path is to see the
    loop drive the tools with no key and no spend.
    """

    def __init__(self) -> None:
        self._script = [
            json.dumps(
                {
                    "thought": "Check the knowledge base for what the ERA Platform is.",
                    "action": "knowledge_search",
                    "action_input": {"query": "What is the ERA Platform?"},
                }
            ),
            json.dumps(
                {
                    "thought": "Now compute 6 times 7 with the sandbox.",
                    "action": "execute_python",
                    "action_input": {"code": "print(6 * 7)"},
                }
            ),
            json.dumps(
                {
                    "thought": "I have both parts and can answer.",
                    "action": "finish",
                    "action_input": {
                        "answer": (
                            "The ERA Platform is an Enterprise Research and Analysis "
                            "Platform — a five-agent LangGraph research system. And 6 x 7 = 42."
                        )
                    },
                }
            ),
        ]
        self._i = 0

    def invoke(self, prompt: str) -> str:  # noqa: ARG002 — prompt ignored on purpose
        response = self._script[min(self._i, len(self._script) - 1)]
        self._i += 1
        return response


class _CannedSearchProvider:
    """A fake ``SearchProvider`` so the offline demo's web tool needs no network."""

    def search(self, query: str, *, max_results: int) -> list[SearchHit]:
        return [
            SearchHit(
                title="ERA Platform",
                url="https://example.com/era",
                content="The ERA Platform is a five-agent research system (canned offline result).",
            )
        ]


def _build_knowledge_tool(embedder: object) -> KnowledgeSearchTool:
    collection = get_ephemeral_collection("exercise-4e")
    knowledge_agent = KnowledgeRetrievalAgent(embedder, collection)  # type: ignore[arg-type]
    indexed = knowledge_agent.ingest_documents(SAMPLE_DOCS)
    logger.info("Indexed %d chunks into the knowledge base.", indexed)
    return KnowledgeSearchTool(knowledge_agent, top_k=2)


async def main() -> None:
    load_dotenv()

    if os.environ.get("GOOGLE_API_KEY"):
        logger.info("GOOGLE_API_KEY found — the real Gemini model will drive the loop.")
        from era_platform.rag import GeminiEmbedder

        llm: object = _GeminiLLM()
        embedder: object = GeminiEmbedder()
        primary: SearchProvider | None = (
            TavilyProvider() if os.environ.get("TAVILY_API_KEY") else None
        )
        web_tool = WebSearchTool(primary, DuckDuckGoProvider())
    else:
        logger.warning("No GOOGLE_API_KEY — using a scripted planner and offline tools.")
        llm = _ScriptedPlanner()
        embedder = _LocalEmbedder()
        web_tool = WebSearchTool(_CannedSearchProvider(), None)

    tools = [web_tool, CodeExecutionTool(), _build_knowledge_tool(embedder)]
    agent = ResearchAgent(llm, tools)  # type: ignore[arg-type]

    result = await agent.safe_run(question=QUESTION)

    logger.info("Q: %s", result.question)
    logger.info("A: %s", result.answer)
    logger.info("Tools used: %s", ", ".join(result.tools_used) or "(none)")
    logger.info("Stopped because: %s (%d steps)", result.stopped_reason, len(result.steps))


if __name__ == "__main__":
    asyncio.run(main())
