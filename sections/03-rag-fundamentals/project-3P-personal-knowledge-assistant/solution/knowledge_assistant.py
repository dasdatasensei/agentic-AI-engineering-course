"""Project 1 (3.P) — solution: a personal knowledge assistant CLI.

Drives the packaged ``KnowledgeRetrievalAgent`` (in ``era_platform/rag/``). Point
it at a folder of ``.txt`` files, then ask questions across the collection with
hybrid (dense + BM25) retrieval and optional metadata filtering.

Examples:

    python .../solution/knowledge_assistant.py --docs ./my_notes --query "vector databases"
    python .../solution/knowledge_assistant.py --docs ./my_notes --query "deadlines" \\
        --source plan.txt
    python .../solution/knowledge_assistant.py --docs ./my_notes --query "..." --dense-only

With GOOGLE_API_KEY set it uses Gemini embeddings; without one it falls back to a
local bag-of-words embedder so the flow runs offline. Persistence honours
CHROMA_PERSIST_DIR (default ./chroma_db).
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from era_platform.rag import KnowledgeQuery, KnowledgeRetrievalAgent
from era_platform.rag.ingestion import IngestionError
from era_platform.rag.store import get_persistent_collection

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class _LocalEmbedder:
    """Deterministic offline embedder used when no GOOGLE_API_KEY is set."""

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


def _build_embedder() -> object:
    if os.environ.get("GOOGLE_API_KEY"):
        logger.info("GOOGLE_API_KEY found — using Gemini embeddings.")
        from era_platform.rag import GeminiEmbedder

        return GeminiEmbedder()
    logger.warning("No GOOGLE_API_KEY — using the offline local embedder.")
    return _LocalEmbedder()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Personal knowledge assistant (RAG over your docs)."
    )
    parser.add_argument(
        "--docs", type=Path, required=True, help="Directory of .txt documents to index."
    )
    parser.add_argument("--query", required=True, help="The question to ask across the collection.")
    parser.add_argument("--source", default=None, help="Restrict results to this source file name.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of passages to return.")
    parser.add_argument(
        "--dense-only",
        action="store_true",
        help="Disable BM25 hybrid fusion and use pure embedding similarity.",
    )
    parser.add_argument(
        "--collection", default="knowledge_base", help="ChromaDB collection name to use."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = _parse_args(argv)

    embedder = _build_embedder()
    collection = get_persistent_collection(collection_name=args.collection)
    agent = KnowledgeRetrievalAgent(embedder, collection)  # type: ignore[arg-type]

    try:
        indexed = agent.ingest_directory(args.docs)
    except IngestionError as exc:
        logger.error("Ingestion failed: %s", exc)
        return 1
    logger.info("Indexed %d chunks from %s", indexed, args.docs)

    where = {"source": args.source} if args.source else None
    query = KnowledgeQuery(
        question=args.query, top_k=args.top_k, where=where, hybrid=not args.dense_only
    )
    hits = agent.retrieve(query)

    if not hits:
        logger.info("No relevant passages found for %r.", args.query)
        return 0

    mode = "dense-only" if args.dense_only else "hybrid"
    print(f"\nTop {len(hits)} passages ({mode}) for: {args.query!r}\n")
    for rank, hit in enumerate(hits, start=1):
        source = hit.metadata.get("source", "unknown")
        print(f"[{rank}] score={hit.score:.4f}  source={source}")
        print(f"    {hit.text.strip()[:300]}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
