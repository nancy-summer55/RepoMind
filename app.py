"""RepoMind - Streamlit UI: guided repository learning and source inspection.

Chat runs the retrieval backend (repo_rag.hybrid_search()) followed by the
Guided Q&A orchestration layer (intent classification, source labeling, and a
grounded answer prompt) before calling DeepSeek. Answers cite [Source N] and
are inspectable via the source inspector and retrieval debug.

No retrieval algorithm was changed. repo_rag.hybrid_search() remains the
retrieval backend; the Learning modules orchestrate answers around it.
Learning Map generation reuses the same backend client config.
"""

import os
import re
from pathlib import Path

import streamlit as st
from dotenv import dotenv_values

from learning.deepseek_adapter import (
    build_deepseek_llm_callable,
    generate_repository_learning_map_with_client,
)
from learning.guided_qna import (
    build_guided_answer_artifacts,
    finalize_guided_answer,
)
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

    repo_rag is cached here so backend state is reused across Streamlit reruns.
    """
    from repo_rag import (
        DEEPSEEK_MODEL,
        get_collection,
        get_deepseek_client,
        hybrid_search,
        index_repository,
    )

    return (
        index_repository,
        get_collection,
        hybrid_search,
        get_deepseek_client,
        DEEPSEEK_MODEL,
    )


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
if "selected_source_index" not in st.session_state:
    st.session_state.selected_source_index = None
if "learning_map" not in st.session_state:
    st.session_state.learning_map = None
if "project_profile" not in st.session_state:
    st.session_state.project_profile = None
if "file_profiles" not in st.session_state:
    st.session_state.file_profiles = []
if "learning_sources" not in st.session_state:
    st.session_state.learning_sources = []
if "learning_prompt" not in st.session_state:
    st.session_state.learning_prompt = ""
if "learning_error" not in st.session_state:
    st.session_state.learning_error = None

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
    "there is no",
    "does not exist",
    "is not defined",
    "cannot be found",
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


def _detect_user_language(text: str) -> str:
    """Choose the guided answer language from the user's question."""

    return "Chinese" if re.search(r"[\u4e00-\u9fff]", text or "") else "English"


def _merge_labeled_sources(search_results: list[dict], labeled_sources) -> list[dict]:
    """Preserve raw retrieval debug while adding source role metadata."""

    merged_results = []
    for result, source in zip(search_results, labeled_sources):
        merged = dict(result)
        metadata = dict(merged.get("metadata", {}))
        metadata["source_role"] = source.source_role
        metadata["relevance_reason"] = source.relevance_reason
        merged["metadata"] = metadata
        merged_results.append(merged)

    if len(search_results) > len(merged_results):
        merged_results.extend(search_results[len(merged_results) :])

    return merged_results


def _get_preflight_issues() -> list[tuple[str, str]]:
    """Run static runtime checks without loading models or calling DeepSeek."""

    env_path = Path(__file__).resolve().parent / ".env"
    env_values = (
        dotenv_values(env_path)
        if env_path.exists()
        else {}
    )

    api_key = str(
        env_values.get("DEEPSEEK_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
        or ""
    ).strip()
    embedding_model_path = str(
        env_values.get("EMBEDDING_MODEL_PATH")
        or os.getenv("EMBEDDING_MODEL_PATH")
        or ""
    ).strip()

    issues = []

    if not api_key or api_key == "your_deepseek_api_key_here":
        issues.append(
            (
                "warning",
                "DEEPSEEK_API_KEY is missing or still uses the placeholder. "
                "Guided Q&A and Learning Map generation will fail until it is "
                "configured in .env.",
            )
        )

    if embedding_model_path:
        local_model_path = Path(embedding_model_path).expanduser()
        if not local_model_path.exists() or not local_model_path.is_dir():
            issues.append(
                (
                    "error",
                    "EMBEDDING_MODEL_PATH is set but invalid. Indexing will fail "
                    "until it points to an existing local model directory.",
                )
            )

    return issues


def _render_preflight_warnings() -> None:
    """Show user-friendly runtime warnings before indexing or asking."""

    for level, message in _get_preflight_issues():
        if level == "error":
            st.error(message)
        else:
            st.warning(message)


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
    (
        index_repository_fn,
        get_collection_fn,
        _,
        get_deepseek_client_fn,
        deepseek_model,
    ) = get_backend()

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
        st.session_state.selected_source_index = None
        st.session_state.learning_map = None
        st.session_state.project_profile = None
        st.session_state.file_profiles = []
        st.session_state.learning_sources = []
        st.session_state.learning_prompt = ""
        st.session_state.learning_error = None

        try:
            learning_artifacts = generate_repository_learning_map_with_client(
                repo_path=str(root),
                client_factory=get_deepseek_client_fn,
                model_name=deepseek_model,
                chunk_size=INDEX_CHUNK_SIZE,
                chunk_overlap=INDEX_CHUNK_OVERLAP,
                chunk_strategy=INDEX_CHUNK_STRATEGY,
                user_language="Chinese",
            )
            st.session_state.learning_map = learning_artifacts["learning_map"]
            st.session_state.project_profile = learning_artifacts["project_profile"]
            st.session_state.file_profiles = learning_artifacts["file_profiles"]
            st.session_state.learning_sources = learning_artifacts["sources"]
            st.session_state.learning_prompt = learning_artifacts["prompt"]
        except Exception as error:
            st.session_state.learning_map = None
            st.session_state.learning_error = str(error)

    except ValueError as error:
        st.session_state.index_error = str(error)
        st.session_state.index_status = "error"
    except Exception as error:
        message = str(error)
        if "Embedding model local path" in message or "Failed to load embedding model" in message:
            st.session_state.index_error = (
                "Indexing failed because the embedding model is not available. "
                "Check EMBEDDING_MODEL_PATH or the local Hugging Face cache/network."
            )
        else:
            st.session_state.index_error = f"Indexing failed: {error}"
        st.session_state.index_status = "error"


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
def ask(prompt: str) -> None:
    """Run Guided Q&A over the existing hybrid retrieval results."""

    st.session_state.messages.append({"role": "user", "content": prompt})

    _, _, hybrid_search_fn, get_deepseek_client_fn, deepseek_model = get_backend()

    try:
        with st.status(
            "Searching repository and generating answer…", expanded=True
        ) as status:
            search_results = hybrid_search_fn(
                query=prompt,
                top_k=RAG_TOP_K,
            )
            if not search_results:
                raise ValueError("No relevant repository content was found.")

            guided_artifacts = build_guided_answer_artifacts(
                question=prompt,
                retrieval_results=search_results,
                user_language=_detect_user_language(prompt),
            )
            labeled_search_results = _merge_labeled_sources(
                search_results,
                guided_artifacts["sources"],
            )
            llm_callable = build_deepseek_llm_callable(
                get_deepseek_client_fn,
                deepseek_model,
            )
            answer = llm_callable(guided_artifacts["prompt"])
            answer_result = finalize_guided_answer(
                intent_result=guided_artifacts["intent_result"],
                answer_text=answer,
                sources=guided_artifacts["sources"],
                retrieval_results=labeled_search_results,
                followups=guided_artifacts["followups"],
            )
            status.update(label="Answer ready", state="complete", expanded=False)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer_result.answer,
                "sources": labeled_search_results,
                "followups": answer_result.followups,
                "intent": answer_result.intent,
                "refusal": answer_result.refusal or _is_refusal(answer_result.answer),
            }
        )
        st.session_state.current_sources = labeled_search_results
        st.session_state.current_retrieval_results = labeled_search_results
        st.session_state.selected_message_index = len(st.session_state.messages) - 1
        st.session_state.selected_source_index = None

    except Exception as error:
        message = str(error)
        if "DEEPSEEK_API_KEY" in message:
            user_message = (
                "Guided Q&A failed because DEEPSEEK_API_KEY is missing or invalid. "
                "Your repository index is still available."
            )
        else:
            user_message = (
                "Guided Q&A failed, but your repository index is still "
                f"available. Error: {error}"
            )
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": user_message,
                "error": True,
                "sources": [],
                "followups": [],
                "intent": "",
                "refusal": False,
            }
        )
        st.session_state.current_sources = []
        st.session_state.current_retrieval_results = []
        st.session_state.selected_message_index = len(st.session_state.messages) - 1
        st.session_state.selected_source_index = None


def clear_conversation() -> None:
    """Clear only the chat; the repository index stays intact."""
    st.session_state.messages = []
    st.session_state.current_sources = []
    st.session_state.current_retrieval_results = []
    st.session_state.selected_message_index = None
    st.session_state.selected_source_index = None


def render_learning_map_preview() -> str | None:
    """Render minimal Learning Map state above the existing chat."""

    learning_map = st.session_state.learning_map
    if learning_map is not None:
        st.markdown("#### Learning Map")
        if learning_map.project_summary:
            st.markdown(learning_map.project_summary)
        if learning_map.starter_questions:
            st.markdown("Starter questions")
            for index, question in enumerate(learning_map.starter_questions):
                if st.button(
                    question,
                    key=f"learning_starter_{index}",
                    width="stretch",
                ):
                    return question
        st.divider()
        return None

    if st.session_state.learning_error:
        st.warning(
            "Repository indexed, but Learning Map generation failed: "
            f"{st.session_state.learning_error}"
        )
        st.divider()

    return None


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="RepoMind",
    page_icon="\u25cc",
    layout="wide",
)

styles.apply_styles()

_render_preflight_warnings()

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
    starter_question = render_learning_map_preview()
    if starter_question:
        ask(starter_question)
        st.rerun()
    (
        clear_clicked,
        clicked_message,
        clicked_source,
        followup_question,
    ) = components.render_chat(
        messages=st.session_state.messages,
        index_status=st.session_state.index_status,
    )
    if clear_clicked:
        clear_conversation()
        st.rerun()
    if clicked_message is not None:
        st.session_state.selected_message_index = clicked_message
        st.session_state.selected_source_index = clicked_source
        st.rerun()
    if followup_question:
        ask(followup_question)
        st.rerun()
    prompt = st.chat_input(
        "Ask about this repository...",
        disabled=(st.session_state.index_status != "indexed"),
    )
    if prompt:
        ask(prompt)
        st.rerun()

with inspector_col:
    components.render_source_inspector(
        messages=st.session_state.messages,
        selected_message_index=st.session_state.selected_message_index,
        selected_source_index=st.session_state.selected_source_index,
    )
