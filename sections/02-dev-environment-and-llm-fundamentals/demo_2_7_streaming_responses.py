"""Streaming responses: printing chunks as they arrive from the model
instead of waiting for the full response, and framing each one the way a
real Server-Sent Events endpoint would send it.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from langchain_core.messages import AIMessageChunk
from langchain_google_genai import ChatGoogleGenerativeAI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-3.1-flash-lite"
INPUT_PRICE_PER_MILLION = 0.30  # USD — confirm at ai.google.dev/gemini-api/docs/pricing
OUTPUT_PRICE_PER_MILLION = 2.50  # USD

STREAM_PROMPT = "Explain what Server-Sent Events are, in three short paragraphs."


class EmptyStreamError(Exception):
    """Raised when a stream ends without sending a single chunk."""


def to_sse_event(chunk_text: str) -> str:
    """Frame one piece of text the way a real SSE endpoint would send it."""
    data = chunk_text.replace("\n", "\ndata: ")
    return f"data: {data}\n\n"


def stream_and_collect(llm: ChatGoogleGenerativeAI, prompt: str) -> tuple[str, AIMessageChunk]:
    """Stream a response chunk by chunk, printing each one as an SSE event
    and accumulating the full message for logging."""
    full_chunk: AIMessageChunk | None = None
    pieces: list[str] = []

    for chunk in llm.stream(prompt):
        pieces.append(chunk.text)
        print(to_sse_event(chunk.text), end="", flush=True)
        full_chunk = chunk if full_chunk is None else full_chunk + chunk

    if full_chunk is None:
        raise EmptyStreamError("The model sent no chunks.")
    return "".join(pieces), full_chunk


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """Return the cost in USD for one call, given its token usage."""
    input_cost = (input_tokens / 1_000_000) * INPUT_PRICE_PER_MILLION
    output_cost = (output_tokens / 1_000_000) * OUTPUT_PRICE_PER_MILLION
    return input_cost + output_cost


def check_api_key() -> bool:
    """Confirm GOOGLE_API_KEY is present before we ever construct the model."""
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error(
            "GOOGLE_API_KEY not found. Check your .env file against .env.example (Section 2.2)."
        )
        return False
    logger.info("GOOGLE_API_KEY found.")
    return True


def main() -> int:
    """Run the guard rail, then stream one response, framing and logging it."""
    load_dotenv()
    if not check_api_key():
        return 1

    llm = ChatGoogleGenerativeAI(model=MODEL_NAME)
    full_text, final_chunk = stream_and_collect(llm, STREAM_PROMPT)

    usage = final_chunk.usage_metadata
    if usage is None:
        logger.error("The stream finished without token usage.")
        return 1
    cost = calculate_cost(usage["input_tokens"], usage["output_tokens"])

    logger.info(
        "[STREAMED] %d chars | %d in + %d out | $%.6f",
        len(full_text),
        usage["input_tokens"],
        usage["output_tokens"],
        cost,
    )
    logger.info("Streaming complete — ready for Section 2.8.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
