import logging
import os
import sys

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Structured Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)

# Silence noisy default INFO logs from underlying HTTP/API libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)

# Configuration
MODEL_NAME = "gemini-3.1-flash-lite"
CONTEXT_WINDOW_TOKENS = 1_048_576
INPUT_PRICE_PER_MILLION = 0.25
OUTPUT_PRICE_PER_MILLION = 1.50

# Prompts
REVIEW_PROMPT = (
    "Classify the sentiment of this product review and respond with "
    "exactly one word — Positive, Negative, or Mixed.\n\n"
    'Review: "The battery life is incredible but the screen scratches so easily."'
)

REASONING_PROMPT = (
    "A store had 23 notebooks. They sold 9 in the morning and received a "
    "shipment of 15 more in the afternoon, then sold 6 more before closing. "
    "How many notebooks are left?"
)

SYSTEM_PROMPT = (
    "You are a terse product-review classifier. Respond with exactly one "
    "word — Positive, Negative, or Mixed — and nothing else."
)

# Few Shot Examples
FEW_SHOT_EXAMPLES = [
    HumanMessage(content='Review: "Fast shipping, arrived broken."'),
    AIMessage(content="Mixed"),
    HumanMessage(content='Review: "Exactly as described, five stars."'),
    AIMessage(content="Positive"),
]

# Helper Functions


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Return the cost in USD for one call, given its token usage.
    """
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


def run_variant(label: str, llm: ChatGoogleGenerativeAI, messages) -> None:
    """
    Invoke one prompt variant and log its response, token usage, and cost.
    """
    response = llm.invoke(messages)
    usage = response.usage_metadata

    # Clean up response content (handles newer Gemini dict/list formats)
    raw_content = response.content
    if isinstance(raw_content, list) and len(raw_content) > 0 and isinstance(raw_content[0], dict):
        clean_text = raw_content[0].get("text", str(raw_content))
    else:
        clean_text = str(raw_content)

    input_tokens = usage["input_tokens"]
    output_tokens = usage["output_tokens"]
    total_tokens = usage["total_tokens"]
    remaining = CONTEXT_WINDOW_TOKENS - total_tokens
    cost = calculate_cost(input_tokens, output_tokens)

    # .replace keeps the Chain-of-Thought response on a single readable log line
    logger.info("[%s] Response: %s", label, clean_text.strip().replace("\n", " "))
    logger.info(
        "[%s] Tokens: %d in + %d out = %d total (%s of %s window remaining)",
        label,
        input_tokens,
        output_tokens,
        total_tokens,
        f"{remaining:,}",
        f"{CONTEXT_WINDOW_TOKENS:,}",
    )
    logger.info("[%s] Cost: $%.6f", label, cost)


# Main Execution
def main() -> int:
    """Run the guard rail then compare four prompting techniques live."""

    load_dotenv()  # Load environment variables from .env file

    # Fail fast guardrail
    if not check_api_key():
        return 1

    # Instantiate the model only once
    llm = ChatGoogleGenerativeAI(model=MODEL_NAME)

    # 1. Baseline (Raw String - Langchain wraps this automatically)
    run_variant("BASELINE", llm, REVIEW_PROMPT)

    # 2. System Role
    run_variant(
        "SYSTEM ROLE",
        llm,
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=REVIEW_PROMPT),
        ],
    )

    # 3. Few Shot
    run_variant(
        "FEW SHOT",
        llm,
        [
            SystemMessage(content=SYSTEM_PROMPT),
            *FEW_SHOT_EXAMPLES,
            HumanMessage(content=REVIEW_PROMPT),
        ],
    )

    # 4. Chain-of-Thought
    cot_prompt = (
        REASONING_PROMPT + "\n\nThink through this step by step, then give the final answer "
        "on its own line as 'Answer: <number>'."
    )
    run_variant("CHAIN-OF-THOUGHT", llm, cot_prompt)

    logger.info("Prompt Engineering Comparison Complete - You are ready for Section 2.5!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
