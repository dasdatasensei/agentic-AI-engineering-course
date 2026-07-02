"""Project 1 (3.P) — starter: a personal knowledge assistant CLI.

Assemble a command-line knowledge assistant on top of the packaged
``KnowledgeRetrievalAgent`` (in ``era_platform/rag/``). The retrieval logic is
already built and tested in the package — your job here is the thin CLI *driver*:
parse arguments, wire up the agent, ingest a folder, run a query, print results.

Fill in every ``TODO``, adding the imports each step needs. When it works,
compare against ``solution/knowledge_assistant.py``.

Concepts you are applying: 3.5 (metadata filtering) and 3.6 (hybrid dense+BM25
retrieval), both exposed through ``era_platform.rag.KnowledgeQuery``.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class _LocalEmbedder:
    """A deterministic offline embedder, provided so you can build the CLI without a key.

    Swap this for ``era_platform.rag.GeminiEmbedder`` once you have a
    GOOGLE_API_KEY (the solution picks between them automatically).
    """

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


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """TODO: build an ArgumentParser with these options and return the parsed args:

    --docs      (Path, required)    directory of .txt documents to index
    --query     (str, required)     the question to ask across the collection
    --source    (str, optional)     restrict results to this source file name
    --top-k     (int, default 5)    number of passages to return
    --dense-only (store_true)       disable BM25 hybrid fusion (pure dense)
    """
    raise NotImplementedError("Implement _parse_args")


def main(argv: list[str] | None = None) -> int:
    """Drive the assistant end to end.

    TODO — implement the following, importing what each step needs from
    ``era_platform.rag``:

      1. ``args = _parse_args(argv)``.
      2. Build an embedder: ``_LocalEmbedder()`` (or ``GeminiEmbedder()`` when
         ``GOOGLE_API_KEY`` is set).
      3. ``collection = get_persistent_collection()`` (from ``era_platform.rag.store``).
      4. ``agent = KnowledgeRetrievalAgent(embedder, collection)``.
      5. ``agent.ingest_directory(args.docs)`` — catch ``IngestionError`` and exit 1.
      6. Build a ``KnowledgeQuery(question=args.query, top_k=args.top_k,
         where={"source": args.source} if args.source else None,
         hybrid=not args.dense_only)``.
      7. ``agent.retrieve(query)`` and print each hit's rank, score, source, and text.
      8. Return an exit code (0 on success).
    """
    raise NotImplementedError("Wire up the agent, ingest, query, and print results")


if __name__ == "__main__":
    sys.exit(main())
