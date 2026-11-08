"""
demo_2_3_first_llm_call.py
First live LLM call: sends one prompt to Gemini 3.1 Flash Lite, then reports
the exact tokens used and the exact dollar cost of that single call.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-3.1-flash-lite"
CONTEXT_WINDOW_TOKENS = 1_048_576
INPUT_PRICE_PER_MILLION = 0.30  # USD
OUTPUT_PRICE_PER_MILLION = 2.50  # USD


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


def call_llm(prompt: str) -> None:
    """Make one call to Gemini 3.1 Flash Lite and report tokens + cost."""
    llm = ChatGoogleGenerativeAI(model=MODEL_NAME)
    response = llm.invoke(prompt)
    usage = response.usage_metadata
    input_tokens = usage["input_tokens"]
    output_tokens = usage["output_tokens"]
    total_tokens = usage["total_tokens"]
    remaining = CONTEXT_WINDOW_TOKENS - total_tokens
    cost = calculate_cost(input_tokens, output_tokens)

    logger.info("Response: %s", response.content)
    logger.info(
        "Tokens: %d in + %d out = %d total (%s of %s window remaining)",
        input_tokens,
        output_tokens,
        total_tokens,
        f"{remaining:,}",
        f"{CONTEXT_WINDOW_TOKENS:,}",
    )
    logger.info("Cost: $%.6f", cost)


def main() -> int:
    """Run the guard rail, then make one live call if the key is present."""
    load_dotenv()
    if not check_api_key():
        return 1
    call_llm("In one sentence, what is an AI agent?")
    logger.info("First LLM call complete — ready for Section 2.4.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
