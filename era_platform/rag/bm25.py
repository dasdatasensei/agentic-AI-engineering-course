"""A compact, dependency-free BM25 keyword-search index.

Created: 2026-07-02
Last updated: 2026-07-02

Lecture 3.6 teaches *hybrid* retrieval — combining dense (embedding) similarity
with sparse keyword matching. The keyword half is BM25, the standard ranking
function behind Lucene/Elasticsearch. Rather than add a third-party dependency
(``rank-bm25``) for one concept, this module implements BM25 Okapi in ~60 lines
of pure Python, consistent with the foundations phase's "build it by hand so you
understand what the library is doing" pedagogy (the same reason Section 3's
chunking starts hand-rolled before the LlamaIndex node parser is introduced).

BM25 scores a document ``D`` against a query ``Q`` as::

    score(D, Q) = Σ_{t in Q}  IDF(t) · ( f(t,D)·(k1+1) )
                                        ─────────────────────────────────
                                        f(t,D) + k1·(1 − b + b·|D|/avgdl)

where ``f(t,D)`` is the term frequency in ``D``, ``|D|`` the document length,
``avgdl`` the mean document length, and ``k1``/``b`` the standard tuning
constants. The IDF uses the BM25-with-floor variant so a term appearing in every
document contributes a small positive weight rather than a negative one.

This index is scored entirely offline and holds no external state, so it is
trivially unit-testable without a network call or a vector store.
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Standard BM25 Okapi tuning constants (Robertson & Zaragoza, 2009).
DEFAULT_K1 = 1.5
DEFAULT_B = 0.75


def tokenize(text: str) -> list[str]:
    """Lower-case and split ``text`` into alphanumeric tokens.

    A deliberately simple tokenizer: lower-cased ``[a-z0-9]+`` runs. Both
    indexing and querying route through it so their token spaces always match.
    """
    return _TOKEN_RE.findall(text.lower())


class BM25Index:
    """An in-memory BM25 Okapi index over a fixed collection of documents.

    Build it once from a list of document strings, then :meth:`search` it with a
    query to get ``(document_index, score)`` pairs ranked most-relevant first.
    Document indices are positional, so callers can align results back to their
    own chunk metadata.
    """

    def __init__(
        self, documents: list[str], *, k1: float = DEFAULT_K1, b: float = DEFAULT_B
    ) -> None:
        if k1 < 0 or not 0.0 <= b <= 1.0:
            raise ValueError("k1 must be >= 0 and b must be in [0, 1]")
        self._k1 = k1
        self._b = b
        self._doc_token_counts: list[Counter[str]] = [Counter(tokenize(doc)) for doc in documents]
        self._doc_lengths: list[int] = [sum(counts.values()) for counts in self._doc_token_counts]
        self._doc_count = len(documents)
        self._avg_doc_length = sum(self._doc_lengths) / self._doc_count if self._doc_count else 0.0
        self._idf: dict[str, float] = self._compute_idf()
        logger.info(
            "Built BM25 index | docs=%d | avg_len=%.1f | vocab=%d",
            self._doc_count,
            self._avg_doc_length,
            len(self._idf),
        )

    def _compute_idf(self) -> dict[str, float]:
        document_frequency: Counter[str] = Counter()
        for counts in self._doc_token_counts:
            document_frequency.update(counts.keys())
        idf: dict[str, float] = {}
        for term, freq in document_frequency.items():
            # BM25 IDF with a +1 floor so common terms stay weakly positive.
            idf[term] = math.log(1 + (self._doc_count - freq + 0.5) / (freq + 0.5))
        return idf

    def search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        """Return the ``top_k`` best ``(document_index, score)`` pairs for ``query``.

        Documents that share no query term score 0 and are omitted. The result is
        sorted by descending score; ties keep the lower document index first.
        """
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        query_terms = tokenize(query)
        scored: list[tuple[int, float]] = []
        for index, counts in enumerate(self._doc_token_counts):
            score = self._score_document(index, counts, query_terms)
            if score > 0.0:
                scored.append((index, score))
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        return scored[:top_k]

    def _score_document(self, index: int, counts: Counter[str], query_terms: list[str]) -> float:
        doc_length = self._doc_lengths[index]
        length_norm = self._k1 * (
            1 - self._b + self._b * doc_length / self._avg_doc_length
            if self._avg_doc_length
            else 1.0
        )
        score = 0.0
        for term in query_terms:
            term_freq = counts.get(term, 0)
            if term_freq == 0:
                continue
            idf = self._idf.get(term, 0.0)
            score += idf * (term_freq * (self._k1 + 1)) / (term_freq + length_norm)
        return score
