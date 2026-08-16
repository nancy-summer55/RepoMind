"""RepoMind - Streamlit UI, Phase 2: real repository indexing.

Phase 2 connects the Repository panel to the real backend index path:

    path -> index_repository() -> indexed status

Chat / Sources / Retrieval Debug remain mock. No rag() / DeepSeek.
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
    from repo_rag import get_collection, index_repository

    return index_repository, get_collection


# ---------------------------------------------------------------------------
# Index configuration (matches the CLI defaults used for nanoGPT)
# ---------------------------------------------------------------------------
INDEX_CHUNK_SIZE = 1200
INDEX_CHUNK_OVERLAP = 200
INDEX_CHUNK_STRATEGY = "ast"
EMBEDDING_DIMENSION = "768"  # jina-embeddings-v2-base-code

# ---------------------------------------------------------------------------
# Mock data (chat / sources only - indexing is real)
# ---------------------------------------------------------------------------
MOCK_ADVANCED_SETTINGS = {
    "Chunk size": str(INDEX_CHUNK_SIZE),
    "Chunk overlap": str(INDEX_CHUNK_OVERLAP),
    "Top K": "5",
    "RRF K": "60",
}

MOCK_SOURCE = {
    "path": "model.py",
    "qualified_name": "CausalSelfAttention.forward",
    "symbol_type": "method",
    "start_line": 65,
    "end_line": 98,
    "chunk_strategy": "ast_symbol",
}

MOCK_RETRIEVAL_DEBUG = [
    [("Rank", "1")],
    [("Vector rank", "1"), ("Vector similarity", "0.6554")],
    [("BM25 rank", "3")],
    [("RRF rank", "1")],
    [("Strategy", "ast_symbol")],
]

MOCK_MESSAGES = [
    {"role": "user", "content": "How is self-attention implemented?"},
    {
        "role": "assistant",
        "content": (
            "Self-attention is implemented in `CausalSelfAttention`. "
            "The `forward` method projects the input into query, key, "
            "and value representations before applying causal attention."
        ),
        "citations": [1, 2],
    },
]

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
    st.session_state.messages = list(MOCK_MESSAGES)
if "current_sources" not in st.session_state:
    st.session_state.current_sources = [MOCK_SOURCE]
if "backend_notice" not in st.session_state:
    st.session_state.backend_notice = False


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
    index_repository_fn, get_collection_fn = get_backend()

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
    except ValueError as error:
        st.session_state.index_error = str(error)
        st.session_state.index_status = "error"
    except Exception as error:
        st.session_state.index_error = f"Indexing failed: {error}"
        st.session_state.index_status = "error"


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
        advanced=MOCK_ADVANCED_SETTINGS,
        status=st.session_state.index_status,
        error=st.session_state.index_error,
    )
    if index_clicked:
        run_index(path)
        st.rerun()

with chat_col:
    components.render_mock_chat(st.session_state.messages)
    if st.session_state.backend_notice:
        components.render_backend_notice()
    prompt = st.chat_input("Ask about this repository...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.backend_notice = True
        st.rerun()

with inspector_col:
    components.render_source_inspector(
        sources=st.session_state.current_sources,
        retrieval_debug=MOCK_RETRIEVAL_DEBUG,
    )