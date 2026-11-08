"""Multi-provider switching: the same streaming call, the same guard rail,
and the same cost calculation, now working against either Gemini or Groq
behind one shared BaseChatModel interface.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessageChunk
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PROVIDER_MODELS: dict[str, str] = {
    "google": "gemini-3.1-flash-lite",
    "groq": "llama-3.3-70b-versatile",
}

PROVIDER_ENV_KEYS: dict[str, str] = {
    "google": "GOOGLE_API_KEY",
    "groq": "GROQ_API_KEY",
}

PROVIDER_PRICING: dict[str, dict[str, float]] = {
    "google": {
        "input": 0.30,
        "output": 2.50,
    },  # USD/million — ai.google.dev/gemini-api/docs/pricing
    "groq": {"input": 0.59, "output": 0.79},  # USD/million — groq.com/pricing
}

STREAM_PROMPT = "Explain what Server-Sent Events are, in three short paragraphs."


def get_llm(provider: str) -> BaseChatModel:
    """Return a chat model for the given provider, behind one shared interface."""
    if provider not in PROVIDER_MODELS:
        raise ValueError(f"Unknown provider: {provider!r}. Choose 'google' or 'groq'.")
    if provider == "google":
        return ChatGoogleGenerativeAI(model=PROVIDER_MODELS["google"])
    return ChatGroq(model=PROVIDER_MODELS["groq"])


class EmptyStreamError(Exception):
    """Raised when a stream ends without sending a single chunk."""


def to_sse_event(chunk_text: str) -> str:
    """Frame one piece of text the way a real SSE endpoint would send it."""
    data = chunk_text.replace("\n", "\ndata: ")
    return f"data: {data}\n\n"


def stream_and_collect(llm: BaseChatModel, prompt: str) -> tuple[str, AIMessageChunk]:
    """Stream a response chunk by chunk, printing each one as an SSE event
    and accumulating the full message for logging — unchanged from 2.7
    except for the type hint on llm."""
    full_chunk: AIMessageChunk | None = None
    pieces: list[str] = []

    for chunk in llm.stream(prompt):
        pieces.append(chunk.text)
        print(to_sse_event(chunk.text), end="", flush=True)
        full_chunk = chunk if full_chunk is None else full_chunk + chunk

    if full_chunk is None:
        raise EmptyStreamError("The model sent no chunks.")
    return "".join(pieces), full_chunk


def calculate_cost(provider: str, input_tokens: int, output_tokens: int) -> float:
    """Return the cost in USD for one call, using that provider's own pricing."""
    pricing = PROVIDER_PRICING[provider]
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def check_api_key(provider: str) -> bool:
    """Confirm the one API key this provider needs is present."""
    env_var = PROVIDER_ENV_KEYS[provider]
    if not os.getenv(env_var):
        logger.error(
            "%s not found for provider %r. Check your .env file against "
            ".env.example (Section 2.2).",
            env_var,
            provider,
        )
        return False
    logger.info("%s found.", env_var)
    return True


def main() -> int:
    """Run the guard rail for whichever provider was asked for, then stream one response."""
    load_dotenv()
    provider = sys.argv[1] if len(sys.argv) > 1 else "google"

    if provider not in PROVIDER_MODELS:
        logger.error("Unknown provider %r. Choose 'google' or 'groq'.", provider)
        return 1
    if not check_api_key(provider):
        return 1

    llm = get_llm(provider)
    full_text, final_chunk = stream_and_collect(llm, STREAM_PROMPT)

    usage = final_chunk.usage_metadata
    if usage is None:
        logger.error("The stream finished without token usage.")
        return 1
    cost = calculate_cost(provider, usage["input_tokens"], usage["output_tokens"])

    logger.info(
        "[%s] %d chars | %d in + %d out | $%.6f",
        provider.upper(),
        len(full_text),
        usage["input_tokens"],
        usage["output_tokens"],
        cost,
    )
    logger.info("Multi-provider call complete — ready for Exercise 2.E.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
