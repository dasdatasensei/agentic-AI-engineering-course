"""Self-correcting structured outputs: catching the validation failure from
Section 2.5, re-asking the same ChatGoogleGenerativeAI model with the error fed
back in, and bounding the whole thing to a maximum number of attempts.
"""

import logging
import os
import sys
from typing import Any, Literal

from dotenv import load_dotenv
from langchain_core.exceptions import OutputParserException
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-3.1-flash-lite"
INPUT_PRICE_PER_MILLION = 0.30  # USD — confirm at ai.google.dev/gemini-api/docs/pricing
OUTPUT_PRICE_PER_MILLION = 2.50  # USD
MAX_RETRIES = 3

REVIEW_PROMPT = (
    "Classify the sentiment of this product review and explain your reasoning. "
    "Rate your confidence out of 10.\n\n"
    'Review: "The battery life is incredible but the screen scratches so easily."'
)


class ReviewClassification(BaseModel):
    """A validated sentiment classification for one product review."""

    sentiment: Literal["Positive", "Negative", "Mixed"]
    confidence: float = Field(ge=0, le=1)
    reasoning: str


def build_reask_prompt(original_prompt: str, error: Exception) -> str:
    """Feed the model its own validation error and ask it to correct itself."""
    return (
        f"{original_prompt}\n\n"
        "Your previous answer did not satisfy the required schema. "
        f"Pydantic raised this error:\n{error}\n\n"
        "Correct your answer so every field satisfies the schema exactly. "
        "confidence must be a float between 0 and 1 — not a percentage, "
        "not a score out of 10."
    )


def classify_with_retries(
    llm: ChatGoogleGenerativeAI,
    prompt: str,
    max_retries: int = MAX_RETRIES,
) -> tuple[dict[str, Any], int]:
    """Call the model, catching validation failures and re-asking with the
    error fed back in, up to max_retries attempts."""
    structured_llm = llm.with_structured_output(ReviewClassification, include_raw=True)
    current_prompt = prompt

    for attempt in range(1, max_retries + 1):
        try:
            response = structured_llm.invoke(current_prompt)
            # include_raw=True returns the error instead of raising it.
            if response["parsing_error"] is not None:
                raise response["parsing_error"]
        except OutputParserException as exc:
            logger.warning("Attempt %d/%d failed validation: %s", attempt, max_retries, exc)
            if attempt == max_retries:
                raise
            current_prompt = build_reask_prompt(prompt, exc)
            continue

        logger.info("Attempt %d/%d passed validation.", attempt, max_retries)
        return response, attempt

    raise ValueError("max_retries must be at least 1")


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
    """Run the guard rail, then classify one review with bounded self-correction."""
    load_dotenv()
    if not check_api_key():
        return 1

    llm = ChatGoogleGenerativeAI(model=MODEL_NAME)

    try:
        response, attempts_used = classify_with_retries(llm, REVIEW_PROMPT)
    except OutputParserException as exc:
        logger.error(
            "Exhausted %d attempts — model never returned a valid response: %s",
            MAX_RETRIES,
            exc,
        )
        return 1

    result: ReviewClassification = response["parsed"]
    usage = response["raw"].usage_metadata
    cost = calculate_cost(usage["input_tokens"], usage["output_tokens"])

    logger.info(
        '[SELF-CORRECTED] sentiment=%s confidence=%.2f reasoning="%s"',
        result.sentiment,
        result.confidence,
        result.reasoning,
    )
    logger.info(
        "[SELF-CORRECTED] Took %d/%d attempt(s) | Tokens: %d in + %d out | Cost: $%.6f",
        attempts_used,
        MAX_RETRIES,
        usage["input_tokens"],
        usage["output_tokens"],
        cost,
    )
    logger.info("Self-correction complete — ready for Section 2.7.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
