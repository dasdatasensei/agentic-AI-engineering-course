# Exercise 3.E · Answer questions from your own documents

**Section:** 3 · RAG Fundamentals
**Type:** Coding exercise · **Applies:** Lectures 3.1, 3.2, 3.3, 3.4, 3.5

---

## Learning objective

In Section 2 you built a summariser that distils text you hand it. Here you
**upgrade it into a question-answerer grounded in your own documents**: instead
of pasting source text into the prompt, you *retrieve* the relevant passages from
an indexed collection and answer strictly from them. That retrieve-then-answer
shape is what makes RAG fix hallucination (lecture 3.1) — the model is told to
answer only from the supplied context and to say so when the answer isn't there.

By the end you'll have built and proven the **RAG core** the rest of the course
reuses:

1. **Ingestion** — load documents → chunk them → embed each chunk → index into ChromaDB.
2. **Retrieval** — a `similarity_search` that embeds a query and returns the closest chunks.
3. **Grounded answering** — feed the retrieved chunks to an LLM under a strict "context-only" instruction.

## The design mirrors 2.E

Just as the summariser depended on a tiny `LLMClient` protocol, the RAG core
depends on a tiny **`Embedder` protocol** (`embed_documents` / `embed_query`).
That's what keeps it testable with **no network and no API key**: tests inject a
deterministic fake embedder and an in-memory ChromaDB collection. The course
default `GeminiEmbedder` (Gemini via LlamaIndex) is wired only in the `solution/`.

## Where the code lives

| Path | What it is |
|---|---|
| `starter/document_qa.py` | Stubbed single-file scaffold with `TODO`s — **start here.** |
| `solution/document_qa.py` | Runnable demo that drives the packaged reference (real Gemini, with an offline fallback). |
| `era_platform/rag/` | The reference implementation, packaged so it's type-checked and importable by later sections. |
| `tests/unit/test_knowledge_retrieval.py` | The unit tests (repo-root `tests/`). |

> **Note on structure:** the reusable logic lives in the `era_platform.rag`
> package (not duplicated in `solution/`) so it's covered by `mypy --strict` and
> the test suite. The `starter/` is a standalone practice file — build it
> yourself, then compare against the packaged reference. This is the same pilot
> pattern as Exercise 2.E.

## Your task

1. Open `starter/document_qa.py` and implement every `TODO`: `chunk_text`, then
   `DocumentQA.index`, `.retrieve`, and `.answer`.
2. Run the packaged tests to see the reference behaviour you're aiming at (they
   drive the `era_platform.rag` reference with a **fake embedder** — no API key,
   no network, no spend):
   ```bash
   pytest tests/unit/test_knowledge_retrieval.py -v
   ```
3. Run the demo end-to-end:
   ```bash
   python sections/03-rag-fundamentals/exercise-3E-document-qa/solution/document_qa.py
   ```
   With `GOOGLE_API_KEY` set it uses Gemini Embeddings; without one it falls back
   to a local bag-of-words embedder so it still runs offline.

## Acceptance criteria

- [ ] `chunk_text` splits long text into overlapping chunks and rejects `overlap >= chunk_size`.
- [ ] `DocumentQA.index` embeds each chunk and stores it in the ChromaDB collection.
- [ ] `DocumentQA.retrieve` embeds the query and returns the `top_k` closest chunks, most-relevant first.
- [ ] `DocumentQA.answer` returns a "can't answer" response **without calling the LLM** when nothing is retrieved.
- [ ] The retrieved passages actually appear in the prompt sent to the LLM.
- [ ] A failure of the LLM call is wrapped in a custom exception, not raised bare.
- [ ] Uses the standard `logging` module (not `print`) and full type hints.

## Concepts this applies

- **3.1 — Why RAG fixes hallucination:** answer only from retrieved context.
- **3.2 — Embeddings:** turn text into vectors whose distance encodes similarity.
- **3.3 — ChromaDB:** an in-process vector store; cosine distance.
- **3.4 — Ingestion pipeline:** load → chunk → embed → index.
- **3.5 — Retrieval strategies:** top-k similarity search (and, in 3.P, metadata filtering).
