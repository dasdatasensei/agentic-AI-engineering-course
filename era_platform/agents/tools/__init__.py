"""ERA Platform agent tools — the capabilities a ReAct agent can select and call.

Introduced in Section 4 (Exercise 4.E). Every tool implements the small
:class:`~era_platform.agents.tools.base.Tool` contract so
:class:`~era_platform.agents.research_agent.ResearchAgent` can enumerate them,
describe them to its LLM, and dispatch by name:

* :mod:`~era_platform.agents.tools.base` — the ``Tool`` ABC, ``FunctionTool``, the
  ``@tool`` decorator, and ``ToolError`` (lectures 4.1–4.2).
* :mod:`~era_platform.agents.tools.web_search` — Tavily → DuckDuckGo (4.5).
* :mod:`~era_platform.agents.tools.code_execution` — AST-checked subprocess sandbox (4.6).
* :mod:`~era_platform.agents.tools.knowledge_search` — wraps the 3.P
  ``KnowledgeRetrievalAgent`` so the agent can search its own documents.
"""

from era_platform.agents.tools.base import FunctionTool, Tool, ToolError, tool
from era_platform.agents.tools.code_execution import (
    DEFAULT_BLOCKED_NAMES,
    CodeExecutionTool,
    CodeSafetyError,
    assert_code_is_safe,
)
from era_platform.agents.tools.knowledge_search import KnowledgeSearchTool
from era_platform.agents.tools.web_search import (
    DuckDuckGoProvider,
    SearchHit,
    SearchProvider,
    TavilyProvider,
    WebSearchTool,
)

__all__ = [
    "DEFAULT_BLOCKED_NAMES",
    "CodeExecutionTool",
    "CodeSafetyError",
    "DuckDuckGoProvider",
    "FunctionTool",
    "KnowledgeSearchTool",
    "SearchHit",
    "SearchProvider",
    "TavilyProvider",
    "Tool",
    "ToolError",
    "WebSearchTool",
    "assert_code_is_safe",
    "tool",
]
