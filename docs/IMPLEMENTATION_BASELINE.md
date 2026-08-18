# RepoMind Implementation Baseline

Baseline audit date: 2026-08-18.

> **Historical snapshot notice:** This document records the implementation baseline at a specific point in time (2026-08-18). Descriptions of `ask()` / `rag()` and other behavior reflect the code as it existed then; the codebase may have evolved since. For the current architecture and usage, refer to `README.md` and the current source code.

Initial command run from `<project_root>`:

```text
git status --short
```

Result: no output; the visible working tree was clean before this document was added.

## 1. Current Repository Structure

`app.py` is the Streamlit entry point. It owns page setup, session state initialization, repository indexing orchestration, chat orchestration, and the wiring between UI components and backend functions.

`repo_rag.py` is the main backend module. It loads environment variables, loads the embedding model at import time, creates the persistent Chroma client, indexes repositories, performs vector search, builds BM25 corpora, applies RRF fusion and overlap deduplication, calls DeepSeek, and exposes CLI commands.

`repo_loader.py` discovers and reads repository files. It currently supports `.py` and `.md`, ignores common generated/dependency directories, skips files larger than 512 KB, and returns document dictionaries with content and basic metadata.

`ast_chunker.py` implements Python AST-aware chunking and non-Python fallback chunking. It creates stable chunk IDs, symbol metadata, line ranges, embedding-specific `index_text`, local and global chunk indices, and debug/statistics output.

`chunker.py` implements the older fixed line-preserving chunker. It is still used when `repo_rag.index_repository()` is called with `chunk_strategy != "ast"`.

`ui/components.py` contains pure Streamlit rendering functions for the header, repository panel, chat, source inspector, retrieval details, refusal state, and small display helpers.

`ui/styles.py` contains all custom CSS used by the Streamlit UI.

`README.md` documents the current product, default RAG architecture, evaluated limitations, usage, and known future work.

`hybrid_retriever.py` is present but documented as a standalone experimental retriever not used by the current pipeline.

`evaluation/` stores evaluation JSON and Markdown reports. `docs/demo/` stores demo planning and screenshots. `design-system/` stores the visual/interaction design spec. `chroma_db/` is the persistent Chroma store when generated locally, but it is not listed by `rg --files` in the current repository state.

## 2. Current Indexing Flow

The repository path enters the UI through `ui.components.render_repository_panel()`, which returns `(path, index_clicked)` to `app.py`. When the button is clicked, `app.py` calls `run_index(path)` and then `st.rerun()`.

`app.py:run_index()` validates the path before importing the backend. It rejects empty input, missing paths, and non-directory paths through `st.session_state.index_error` and `st.session_state.index_status = "error"`. Only after validation does it call `get_backend()`, which imports `index_repository`, `get_collection`, and `rag` from `repo_rag.py`. This delayed import avoids loading the embedding model for invalid paths.

`repo_rag.index_repository(repo_path, chunk_size, chunk_overlap, chunk_strategy)` calls `repo_loader.load_repository(repo_path)`. The loader resolves the root path, walks it recursively, filters ignored directories in-place, keeps only `.py` and `.md`, skips files over 512 KB, reads UTF-8 with `errors="replace"`, ignores empty files, and returns documents shaped like:

```text
{
  "content": "...",
  "metadata": {
    "path": "relative/path.py",
    "extension": ".py",
    "language": "python"
  }
}
```

Chunking is selected inside `repo_rag.index_repository()`. With the Streamlit default `chunk_strategy="ast"`, `ast_chunker.split_documents_ast()` is used. Otherwise, `chunker.split_documents()` is used.

For Python under AST chunking, `ast_chunker.split_python_document_ast()` parses the file with `ast.parse()`. Top-level functions become `ast_symbol` chunks, classes are processed through `process_class_node()` so methods/nested classes become symbol chunks and class residual code becomes `ast_class_context`, and remaining module-level code becomes `ast_residual`. Large symbols are split by `split_line_range()` as `ast_symbol_split`. Syntax errors fall back to fixed line-range chunks with `chunk_strategy="fixed_fallback"`.

For Markdown under AST chunking, `ast_chunker.split_non_python_document()` calls `split_line_range()` with `chunk_strategy="fixed_markdown"` and `symbol_type="document"`. Generic non-Python files would use `fixed_generic`, but the loader currently only emits Python and Markdown.

For fixed chunking, `chunker.split_documents()` calls `split_document()` for each document. It preserves full lines, targets an approximate character budget, applies character-based overlap by stepping back over prior lines, and stores `path`, `extension`, `language`, `start_line`, `end_line`, and per-file `chunk_index`.

Embeddings are generated in `repo_rag.index_repository()` after chunking. For each chunk, indexing text is `chunk["index_text"]` when present, otherwise `chunk["content"]`. AST chunks create `index_text` with file, symbol, type, and content. The module-level `embedding_model` encodes all texts with `batch_size=32` and `show_progress_bar=True`.

Chroma persistence is configured at import time in `repo_rag.py` with `chromadb.PersistentClient(path=BASE_DIR / "chroma_db")` and collection name `repomind`. During every index run, `create_clean_collection()` deletes the old collection if it exists and creates a new cosine HNSW collection. `index_repository()` saves chunks in batches of 128 using chunk IDs, chunk content as documents, chunk metadata, and generated embeddings.

The index summary shown in the UI is not returned by `repo_rag.index_repository()`. It is generated in `app.py:run_index()` after indexing by calling `get_collection_fn()`, reading `collection.get()["metadatas"]`, and computing repository name, unique file count, `collection.count()`, chunking label, embedding label, and embedding dimension. This summary is stored in `st.session_state.index_summary`.

## 3. Current Question Answering Flow

The user question enters through `st.chat_input()` in `app.py`. When a prompt is submitted, `app.py` calls `ask(prompt)` and then `st.rerun()`.

`app.py:ask()` appends the user message to `st.session_state.messages`, obtains `rag` from `get_backend()`, displays a Streamlit status, and calls:

```text
rag(question=prompt, top_k=5, min_similarity=0)
```

`repo_rag.rag()` calls `hybrid_search(query=question, top_k=top_k)`. If no results are returned, it returns a fixed "No relevant repository content was found." answer with empty results. If `min_similarity > 0`, it applies the legacy vector similarity gate, but the UI sets this to 0, so the gate is disabled in normal Streamlit use.

The current retrieval order in `repo_rag.hybrid_search()` is:

1. `get_collection()` loads the existing Chroma collection.
2. `candidate_k = min(top_k * CANDIDATE_MULTIPLIER, collection.count())`; with default `top_k=5`, this is up to 15.
3. `vector_search_candidates(query, candidate_k)` embeds the query and queries Chroma by cosine distance. It returns IDs, documents, metadata, distance, and similarity.
4. `bm25_search(collection, query, candidate_k)` builds the BM25 corpus from the whole Chroma collection, tokenizes path/symbol/document text, creates a new `BM25Okapi`, scores the query, and returns positive-scoring candidates.
5. `reciprocal_rank_fusion(vector_results, bm25_results, rrf_k=60)` merges both ranked lists by chunk ID, records vector rank, BM25 rank, similarity, distance, BM25 score, RRF score, and `rrf_rank`.
6. `deduplicate_search_results(fused_results, top_k, overlap_threshold=0.30)` removes same-file chunks whose line overlap ratio against already-selected chunks is at least 0.30, preserving fused order.

Although `repo_rag.py` defines `get_reranker_model()` and `rerank_candidates()`, `hybrid_search()` currently does not call `rerank_candidates()`. The active pipeline is vector search, BM25, RRF, dedup, then DeepSeek. Some docstrings still mention a Python Code Reranker, but the active code and README indicate reranker is disabled by default.

`repo_rag.build_context(search_results)` converts final retrieval results into a plain text context. Each result becomes:

```text
[Source N]
File: path
Lines: start-end

chunk document
```

`repo_rag.generate_answer(question, search_results)` calls `build_context()`, constructs a system prompt requiring answers only from retrieved repository context with `[Source N]` citations, constructs a user prompt with the retrieved context and question, creates a DeepSeek client through `get_deepseek_client()`, and calls `client.chat.completions.create(model=DEEPSEEK_MODEL, messages=[...], stream=False)`.

`get_deepseek_client()` reads `DEEPSEEK_API_KEY` from environment variables loaded from `.env` and returns an OpenAI-compatible client with `base_url="https://api.deepseek.com"`. `DEEPSEEK_MODEL` defaults to `deepseek-chat`.

Back in `app.py:ask()`, the returned answer and search results are appended to `st.session_state.messages` as an assistant message with `content`, `sources`, and `refusal`. `refusal` is computed by `_is_refusal(answer)` using text markers. The same results are also written to `current_sources` and `current_retrieval_results`, while `selected_message_index` points to the new assistant message and `selected_source_index` is reset to `None`.

If any exception escapes `rag()`, `app.py:ask()` appends a generic assistant error message, clears current sources/debug results, selects that message, and keeps the repository index state intact.

## 4. Reusable Functions

`repo_loader.load_repository(repo_path)` can be reused as the Learning MVP's file inventory and raw document reader. Input is a repository path. Output is a list of document dictionaries with content and metadata. Reuse it before chunking to compute project and file profiles from complete file text.

`ast_chunker.split_documents_ast(documents, chunk_size=1200, chunk_overlap=200)` can be reused to generate Python symbol-aware chunks and Markdown fixed chunks. Input is the loader's documents. Output is a list of chunks with IDs, content, optional `index_text`, and metadata including path, language, line range, chunk strategy, symbol type/name, qualified name, per-file chunk index, and global chunk index. Reuse it for Learning Map source extraction and source-to-symbol linking.

`chunker.split_documents(documents, chunk_size=1200, chunk_overlap=200)` can be reused as the fallback fixed chunking path. Input is documents. Output is chunks with line ranges and basic metadata. It is useful for parity with current non-AST indexing modes, but it does not provide symbol metadata.

`repo_rag.index_repository(repo_path, chunk_size=1200, chunk_overlap=200, chunk_strategy="fixed")` can be reused as the indexing side-effect operation. Input is repo path and chunking parameters. Output is currently `None`; side effects are Chroma collection replacement and console logging. For Learning MVP, either this function must return artifacts or a wrapper must recompute/read needed artifacts without disrupting indexing.

`repo_rag.hybrid_search(query, top_k=5)` can be reused for guided question retrieval. Input is a natural language query. Output is final deduped search results with document, metadata, vector/BM25/RRF fields, and source order. It should remain the existing retrieval primitive while Learning MVP adds planning/composition around it.

`repo_rag.build_context(search_results)` can be reused by an answer composer when the answer still follows the current source format. Input is search results. Output is the grounded context string for an LLM. For richer guided answers, a new composer can call this or a role-aware variant.

`repo_rag.get_deepseek_client()` can be reused by Learning MVP LLM calls. Input is environment configuration. Output is an OpenAI-compatible client. Reuse should centralize API key handling, but additional callers need their own exception handling.

Existing source inspector functions in `ui.components.py` are reusable for Learning MVP source display. `render_source_inspector(messages, selected_message_index, selected_source_index)` renders selected assistant sources plus retrieval debug. `render_source_item(result, source_number, selected)` renders file, symbol, line metadata, and code preview. `render_retrieval_debug(results)` renders vector, BM25, RRF, chunk strategy, symbol, and lines. Future source role labels can extend these functions later, but this phase does not modify them.

## 5. Learning Map Integration Points

The Learning Map should be generated during the indexing flow after documents and chunks are available, and before `app.py:run_index()` marks the repository as indexed. The best logical point is immediately after `repo_rag.index_repository()` has loaded and chunked the repository, because both complete documents and structured chunks are available there before Chroma persistence finishes.

The Learning Map needs the loader documents for full-file project/file profiling, AST chunks for source-aware topics and symbol/file anchors, and chunk metadata for `path`, `extension`, `language`, `start_line`, `end_line`, `chunk_strategy`, `symbol_type`, `symbol_name`, `qualified_name`, `chunk_index`, and `global_chunk_index`.

The `app.py` integration point is inside `run_index()`, in the `try` block after a successful backend index call and before setting `index_status = "indexed"`. That location can store generated artifacts in session state and can include artifact status in the UI summary later.

`repo_rag.py` currently returns no indexing artifacts. For Learning MVP, `repo_rag.index_repository()` should either return a structured object such as documents/chunks/index stats/learning artifacts or call into a `learning/` builder and return artifacts to `app.py`. Returning artifacts is cleaner than forcing `app.py` to reload and rechunk the repository separately. Any change should be tightly scoped because `repo_rag.py` is already a large module.

Learning Map generation must fail open. If map/profile generation fails after chunks are created, indexing should remain usable: log/capture the error, set Learning Map fields to `None` or empty structures, preserve the Chroma index, and still set `index_status = "indexed"` unless core indexing itself failed.

## 6. Session State Plan

Existing session state fields:

`repository_path`: current repository path string. Initialized near the top of `app.py`. Updated after successful indexing. Should be preserved across chat clears.

`index_status`: one of `not_indexed`, `indexing`, `indexed`, or `error`. Initialized in `app.py`. Updated by indexing validation and success/failure.

`index_summary`: summary dictionary rendered in the repository panel. Initialized to `None`. Rebuilt after successful indexing. Should be cleared or replaced on reindex failure depending on desired UX; current code leaves old summary unless overwritten.

`indexed_repository`: repository display name. Initialized to `None`. Updated after successful indexing.

`index_error`: indexing error message. Initialized to `None`. Set on validation/index exceptions and cleared before indexing.

`messages`: chat history list. Initialized to empty. Cleared on successful reindex and by `clear_conversation()`.

`current_sources`: most recent answer sources. Initialized to empty. Cleared on reindex and chat clear; updated after ask.

`current_retrieval_results`: most recent retrieval results. Initialized to empty. Cleared on reindex and chat clear; updated after ask.

`selected_message_index`: assistant message selected for source inspector. Initialized to `None`. Updated after ask and source button clicks. Cleared on reindex and chat clear.

`selected_source_index`: selected source within the selected assistant message. Initialized to `None`. Updated by source buttons. Cleared after ask, reindex, and chat clear.

Suggested new fields:

`learning_map`: stores the generated repository learning map. Initialize to `None` with other session state fields. Rebuild and replace on successful reindex. Clear on indexing failure only if the failed attempt should not show stale map data.

`project_profile`: stores high-level project facts such as detected languages, major directories, entry points, package/build signals, and recommended learning path. Initialize to `None`. Rebuild on successful reindex. Clear with `learning_map` when changing repository.

`file_profiles`: stores per-file profiles keyed by repository-relative path, including role, symbols, summary, and learning relevance. Initialize to `{}`. Rebuild on successful reindex. Clear when reindexing a new repository.

`selected_learning_source`: stores the selected Learning Map node/file/topic for guided source inspection. Initialize to `None`. Reset on successful reindex, chat clear only if chat and learning selection are intentionally coupled.

`pending_question`: stores a guided follow-up or planned question before it is sent to the chat pipeline. Initialize to `None`. Clear after submission, on successful reindex, and on chat clear.

## 7. Guided Q&A Integration Points

Question intent should be added before retrieval, in `app.py:ask()` or a small wrapper called by `ask()`. It should classify questions such as overview, file role, symbol explanation, trace flow, setup/configuration, debugging, or out-of-scope. The classifier implementation should live in a new `learning/` package, not in `repo_rag.py`.

The query planner should live in `learning/` and use intent plus `learning_map`, `project_profile`, and `file_profiles` to produce one or more retrieval queries. It can call the existing `repo_rag.hybrid_search()` for each query. `repo_rag.py` should keep owning low-level retrieval for now.

The answer composer should live in `learning/`. It can initially call `repo_rag.build_context()` for grounded context, then use `get_deepseek_client()` for the model call. A role-aware composer may later build richer context with source roles, but the current `generate_answer()` should remain the default simple RAG path until the guided path is validated.

The follow-up generator should live in `learning/` and consume the final answer, intent, selected sources, and Learning Map state. It should not be embedded in `repo_rag.py` because follow-ups are product/learning behavior, not retrieval.

The source role labeler should live in `learning/` and operate on documents/chunks/metadata plus retrieval results. It can add labels such as entry point, implementation, config, test, docs, dependency, or example. `repo_rag.py` should not own source role semantics beyond preserving metadata needed by retrieval.

Temporarily retained in `repo_rag.py`: `load_repository` import/use, chunk selection, embedding, Chroma persistence, vector search, BM25, RRF, dedup, `build_context()`, `get_deepseek_client()`, and the current `rag()` entry point.

## 8. Risks And Constraints

`repo_rag.py` is a monolithic module. It mixes environment loading, model loading, Chroma client creation, indexing, retrieval, LLM calls, CLI, and debug printing. Adding Learning MVP logic directly there would increase coupling and make regressions harder to isolate.

The embedding model loads at `repo_rag.py` import time. In Streamlit this is mitigated by `app.py:get_backend()` being cached and called only after path validation, but any import of `repo_rag.py` still triggers model loading. This slows tests, CLI startup, and any future code that only needs helper functions.

Chroma indexing is a full rebuild. `create_clean_collection()` deletes the existing `repomind` collection and recreates it for every index run. There is no incremental indexing, no per-repository collection isolation, and no rollback if persistence fails after deletion.

BM25 appears to be rebuilt on every query. `bm25_search()` calls `load_bm25_corpus()`, tokenizes all Chroma documents, and creates a new `BM25Okapi` per request. This is simple but can become slow for larger repositories.

DeepSeek API failure handling exists only at the UI boundary in `app.py:ask()`. `generate_answer()` and `get_deepseek_client()` raise exceptions directly. The UI catches all exceptions and shows a generic failure while keeping the index available, but CLI calls can fail noisily.

Streamlit rerun behavior is central to correctness. `run_index()`, `ask()`, and source button handlers mutate `st.session_state` and then call `st.rerun()`. New Learning state must be initialized before render, updated before rerun, and cleared carefully on reindex to avoid stale repository artifacts.

Current metadata is enough for basic source display and a first Learning Map: path, language, extension, line range, chunk strategy, symbol type/name, qualified name, chunk indices. It is not enough for robust source roles, dependency graphs, imports/exports, call graph edges, package ownership, test-to-source links, or multi-language symbols.

Encoding/mojibake issues are visible in the current code and docs. Examples include corrupted arrows/ellipsis/line separators in `app.py`, `repo_rag.py`, `ui/components.py`, and `README.md`. Some UI strings such as source line display appear malformed. Future work should avoid broad encoding cleanup during Learning MVP unless it is explicitly scoped.

`hybrid_search()` docstrings still mention a code reranker, and `rerank_candidates()` exists, but the active code does not call it. Documentation and comments can mislead future integration if not checked against execution flow.

`index_summary` is built by reading all metadatas through `collection.get()["metadatas"]`. This is acceptable for small repositories but may be inefficient for large indexes.

## 9. Files To Modify In Next Step

1. `learning/__init__.py` - introduce the Learning package boundary.
2. `learning/map_builder.py` - build Learning Map, project profile, and file profiles from documents/chunks/metadata.
3. `learning/schemas.py` - define plain data structures for learning map/profile artifacts.
4. `app.py` - initialize new session state fields and wire index-time artifact storage.
5. `repo_rag.py` - minimally adjust `index_repository()` to return indexing artifacts or accept/call a Learning builder without changing retrieval behavior.
6. `ui/components.py` - only after backend artifacts exist, add display hooks for Learning Map/source role data.

## 10. Explicitly Deferred Files

`hybrid_retriever.py` remains deferred because it is not used by the active pipeline.

Full call graph generation is deferred. The MVP can use file/symbol metadata and lightweight profiles first.

Multi-language AST support is deferred. Current AST-aware chunking is Python-only and Markdown uses fixed chunks.

MCP integration is deferred.

Local LLM support is deferred. Current generation uses DeepSeek through an OpenAI-compatible client.

Incremental indexing is deferred. Current behavior remains full Chroma collection rebuild.

Learning Map UI polish, intent classification, follow-up generation, query planner, answer composer, and source role labeling are deferred from this baseline audit phase and should be implemented only in later phases.
