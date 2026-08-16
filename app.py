"""RepoMind - Streamlit UI, Phase 3: real RAG chat.

The Repository panel runs the real index and the Chat workspace now
calls the real pipeline:

    question -> rag() -> answer + search_results
                     -> Chat + Sources + Retrieval Debug

No retrieval algorithm was changed. DeepSeek is only called through
repo_rag.rag(); the embedding model stays cached per process.
"""

import os
from pathlib import Path

import streamlit as st

from ui import components, styles

# ---------------------------------------------------------------------------
# Backend model loading
# ---------------------------------------------------------------------------
# Jina is cached locally; when present, force Hugging Face offline mode so
# the model loads without a slow network update check (behavior unchanged).
_JINA_HUB_CACHE = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--jinaai--jina-embeddings-v2-base-code"
)
if _JINA_HUB_CACHE.exists():
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


@st.cache_resource
def get_backend():
    """Import the retrieval backend once per process.

    The embedding model is loaded at repo_rag import time, so caching this
    import is what prevents Jina from reloading on every Streamlit rerun.
    """
    from repo_rag import get_collection, index_repository, rag

    return index_repository, get_collection, rag


# ---------------------------------------------------------------------------
# Index configuration (matches the CLI defaults used for nanoGPT)
# ---------------------------------------------------------------------------
INDEX_CHUNK_SIZE = 1200
INDEX_CHUNK_OVERLAP = 200
INDEX_CHUNK_STRATEGY = "ast"
EMBEDDING_DIMENSION = "768"  # jina-embeddings-v2-base-code

RAG_TOP_K = 5
RAG_MIN_SIMILARITY = 0  # keep the same gate the backend evaluation uses

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "repository_path" not in st.session_state:
    st.session_state.repository_path = ""
if "index_status" not in st.session_state:
    st.session_state.index_status = "not_indexed"
if "index_summary" not in st.session_state:
    st.session_state.index_summary = None
if "indexed_repository" not in st.session_state:
    st.session_state.indexed_repository = None
if "index_error" not in st.session_state:
    st.session_state.index_error = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_sources" not in st.session_state:
    st.session_state.current_sources = []
if "current_retrieval_results" not in st.session_state:
    st.session_state.current_retrieval_results = []
if "selected_message_index" not in st.session_state:
    st.session_state.selected_message_index = None

# ---------------------------------------------------------------------------
# Refusal detection
# ---------------------------------------------------------------------------
_REFUSAL_MARKERS = (
    "insufficient",
    "cannot answer",
    "can't answer",
    "cannot determine",
    "unable to answer",
    "cannot find",
    "cannot provide",
    "no mention",
    "not mentioned",
    "not discussed",
    "not present",
    "does not contain",
    "not enough information",
    "not found in the provided",
    "no relevant repository",
)


def _is_refusal(answer: str) -> bool:
    """Text-level detection of DeepSeek's explicit refusal wording.

    This is not a similarity threshold and does not add any hard-coded
    retrieval rule; it only decides how the answer is presented.
    """
    text = (answer or "").lower()
    return any(marker in text for marker in _REFUSAL_MARKERS)


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------
def run_index(path: str) -> None:
    """Validate the path, run the real index, store the summary in state."""

    if not path or not path.strip():
        st.session_state.index_error = "Repository path not found."
        st.session_state.index_status = "error"
        return

    root = Path(path).expanduser().resolve()

    if not root.exists():
        st.session_state.index_error = "Repository path not found."
        st.session_state.index_status = "error"
        return

    if not root.is_dir():
        st.session_state.index_error = "Repository path is not a directory."
        st.session_state.index_status = "error"
        return

    # Load the backend only after validation so invalid paths
    # never trigger the (slow) embedding model load.
    index_repository_fn, get_collection_fn, _ = get_backend()

    st.session_state.index_status = "indexing"
    st.session_state.index_error = None

    try:
        with st.status("Indexing repository…", expanded=True) as status:
            status.write(
                "Reading files → Creating chunks → "
                "Generating embeddings → Saving index"
            )
            index_repository_fn(
                repo_path=str(root),
                chunk_size=INDEX_CHUNK_SIZE,
                chunk_overlap=INDEX_CHUNK_OVERLAP,
                chunk_strategy=INDEX_CHUNK_STRATEGY,
            )
            collection = get_collection_fn()
            metadatas = collection.get()["metadatas"]
            st.session_state.index_summary = {
                "Repository": root.name,
                "Files": str(len({meta["path"] for meta in metadatas})),
                "Chunks": str(collection.count()),
                "Chunking": "AST",
                "Embedding": "Jina Code",
                "Embedding dim": EMBEDDING_DIMENSION,
            }
            st.session_state.indexed_repository = root.name
            st.session_state.repository_path = str(root)
            st.session_state.index_status = "indexed"
            status.update(
                label=f"Indexed {root.name}",
                state="complete",
                expanded=False,
            )

        # A new repository must not mix with the previous one's chat.
        st.session_state.messages = []
        st.session_state.current_sources = []
        st.session_state.current_retrieval_results = []
        st.session_state.selected_message_index = None

    except ValueError as error:
        st.session_state.index_error = str(error)
        st.session_state.index_status = "error"
    except Exception as error:
        st.session_state.index_error = f"Indexing failed: {error}"
        st.session_state.index_status = "error"


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
def ask(prompt: str) -> None:
    """Run the real rag() pipeline and store the result in session state."""

    st.session_state.messages.append({"role": "user", "content": prompt})

    _, _, rag_fn = get_backend()

    try:
        with st.status(
            "Searching repository and generating answer…", expanded=True
        ) as status:
            answer, search_results = rag_fn(
                question=prompt,
                top_k=RAG_TOP_K,
                min_similarity=RAG_MIN_SIMILARITY,
            )
            status.update(label="Answer ready", state="complete", expanded=False)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "sources": search_results,
                "refusal": _is_refusal(answer),
            }
        )
        st.session_state.current_sources = search_results
        st.session_state.current_retrieval_results = search_results
        st.session_state.selected_message_index = len(st.session_state.messages) - 1

    except Exception:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "The language model request failed. "
                    "Your repository index is still available."
                ),
                "error": True,
                "sources": [],
            }
        )
        st.session_state.current_sources = []
        st.session_state.current_retrieval_results = []
        st.session_state.selected_message_index = len(st.session_state.messages) - 1


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="RepoMind",
    page_icon="\u25cc",
    layout="wide",
)

styles.apply_styles()

components.render_header(
    repo_name=st.session_state.indexed_repository or "No repository",
    status=st.session_state.index_status,
)

repo_col, chat_col, inspector_col = st.columns([0.22, 0.53, 0.25], gap="large")

with repo_col:
    path, index_clicked = components.render_repository_panel(
        initial_path=st.session_state.repository_path,
        summary=st.session_state.index_summary,
        advanced={
            "Chunk size": str(INDEX_CHUNK_SIZE),
            "Chunk overlap": str(INDEX_CHUNK_OVERLAP),
            "Top K": str(RAG_TOP_K),
            "RRF K": "60",
        },
        status=st.session_state.index_status,
        error=st.session_state.index_error,
    )
    if index_clicked:
        run_index(path)
        st.rerun()

with chat_col:
    components.render_chat(
        messages=st.session_state.messages,
        index_status=st.session_state.index_status,
    )
    prompt = st.chat_input(
        "Ask about this repository...",
        disabled=(st.session_state.index_status != "indexed"),
    )
    if prompt:
        ask(prompt)
        st.rerun()

with inspector_col:
    components.render_source_inspector(
        sources=st.session_state.current_sources,
    )
