"""Structured outputs with Pydantic: defining a response schema and binding
it to the same ChatGoogleGenerativeAI call from Sections 2.3 and 2.4, with
validated fields and cost logged for the single call.
"""

import logging
import os
import sys
from typing import Literal

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

REVIEW_PROMPT = (
    "Classify the sentiment of this product review and explain your reasoning.\n\n"
    'Review: "The battery life is incredible but the screen scratches so easily."'
)


class ReviewClassification(BaseModel):
    """A validated sentiment classification for one product review."""

    sentiment: Literal["Positive", "Negative", "Mixed"]
    confidence: float = Field(ge=0, le=1)
    reasoning: str


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
    """Run the guard rail, then classify one review as a validated object."""
    load_dotenv()
    if not check_api_key():
        return 1

    llm = ChatGoogleGenerativeAI(model=MODEL_NAME)
    structured_llm = llm.with_structured_output(ReviewClassification, include_raw=True)

    try:
        response = structured_llm.invoke(REVIEW_PROMPT)
        # With include_raw=True, LangChain does not raise on a bad answer: it
        # returns parsed=None and puts the error (wrapping Pydantic's
        # ValidationError) in "parsing_error". Raise it so we fail loudly.
        if response["parsing_error"] is not None:
            raise response["parsing_error"]
    except OutputParserException as exc:
        logger.error("Model response failed schema validation: %s", exc)
        return 1

    result: ReviewClassification = response["parsed"]
    usage = response["raw"].usage_metadata
    cost = calculate_cost(usage["input_tokens"], usage["output_tokens"])

    logger.info(
        '[STRUCTURED] sentiment=%s confidence=%.2f reasoning="%s"',
        result.sentiment,
        result.confidence,
        result.reasoning,
    )
    logger.info(
        "[STRUCTURED] Tokens: %d in + %d out = %d total | Cost: $%.6f",
        usage["input_tokens"],
        usage["output_tokens"],
        usage["total_tokens"],
        cost,
    )
    logger.info("Structured output complete — ready for Section 2.6.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
