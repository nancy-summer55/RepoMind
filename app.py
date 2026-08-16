"""RepoMind - Streamlit UI, Phase 1: static UI skeleton.

This phase is intentionally UI-only. No retrieval backend is called:
no rag(), index_repository(), Chroma, Jina embeddings, BM25, RRF,
DeepSeek, or AST chunking. Everything rendered here is mock data.
"""

import streamlit as st

from ui import components, styles

# ---------------------------------------------------------------------------
# Mock data (Phase 1 only)
# ---------------------------------------------------------------------------
MOCK_REPO_NAME = "nanoGPT"
MOCK_REPO_PATH = r"..\target_repos\nanoGPT"
MOCK_REPO_FULL_PATH = r"..\target_repos\nanoGPT"
MOCK_INDEX_STATUS = "Indexed"

MOCK_INDEX_SUMMARY = {
    "Files": "19",
    "Chunks": "90",
    "Chunking": "AST",
    "Embedding": "Jina Code",
}

MOCK_ADVANCED_SETTINGS = {
    "Chunk size": "1200",
    "Chunk overlap": "200",
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
# Session state (mock only, no backend involved)
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = list(MOCK_MESSAGES)
if "repository_path" not in st.session_state:
    st.session_state.repository_path = MOCK_REPO_PATH
if "index_status" not in st.session_state:
    st.session_state.index_status = MOCK_INDEX_STATUS
if "current_sources" not in st.session_state:
    st.session_state.current_sources = [MOCK_SOURCE]
if "backend_notice" not in st.session_state:
    st.session_state.backend_notice = False

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
    repo_name=MOCK_REPO_NAME,
    status=st.session_state.index_status,
)

repo_col, chat_col, inspector_col = st.columns([0.22, 0.53, 0.25], gap="large")

with repo_col:
    components.render_repository_panel(
        path=st.session_state.repository_path,
        full_path=MOCK_REPO_FULL_PATH,
        summary=MOCK_INDEX_SUMMARY,
        advanced=MOCK_ADVANCED_SETTINGS,
    )

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