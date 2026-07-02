"""ERA Platform agents — the ``BaseAgent`` contract and its implementations.

* :mod:`~era_platform.agents.base` — the ``BaseAgent`` ABC and ``AgentError``
  (the Section 4 contract; ``run()`` / ``validate_output()`` / ``safe_run()``).
* :mod:`~era_platform.agents.research_agent` — ``ResearchAgent``, the first
  concrete agent: a ReAct tool-user built in Exercise 4.E.
* :mod:`~era_platform.agents.tools` — the ``Tool`` abstraction and the three
  tools 4.E gives the agent (web search, code execution, knowledge search).
"""

from era_platform.agents.base import AgentError, BaseAgent
from era_platform.agents.research_agent import (
    ReActStep,
    ResearchAgent,
    ResearchResult,
)
from era_platform.agents.tools import (
    CodeExecutionTool,
    CodeSafetyError,
    FunctionTool,
    KnowledgeSearchTool,
    Tool,
    ToolError,
    WebSearchTool,
    tool,
)

__all__ = [
    "AgentError",
    "BaseAgent",
    "CodeExecutionTool",
    "CodeSafetyError",
    "FunctionTool",
    "KnowledgeSearchTool",
    "ReActStep",
    "ResearchAgent",
    "ResearchResult",
    "Tool",
    "ToolError",
    "WebSearchTool",
    "tool",
]
