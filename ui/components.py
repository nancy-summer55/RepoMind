"""Reusable Streamlit UI components for RepoMind.

Pure UI: every function renders the data it receives and never touches
the retrieval backend. Phase 3 renders real rag() search results.
"""

import html
import re

import streamlit as st

_INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def _render_body(text: str) -> str:
    """Escape HTML, then turn `code` spans into <code> tags."""
    escaped = html.escape(text)
    return _INLINE_CODE_RE.sub(r"<code>\1</code>", escaped)


def _fmt(value: object) -> str:
    """Format a retrieval field for display; None becomes N/A.

    Numbers keep their raw value (similarity is never shown as a percent).
    """
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    try:
        number = float(value)
        if number.is_integer():
            return str(int(number))
        return f"{number:.4f}"
    except (TypeError, ValueError):
        return str(value)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------


def render_header(repo_name: str = "", status: str = "") -> None:
    if status == "indexed":
        label = "Indexed"
        dot_class = "rm-dot"
    elif status == "indexing":
        label = "Indexing…"
        dot_class = "rm-dot-off"
    else:
        label = "Not indexed"
        dot_class = "rm-dot-off"
    st.markdown(
        f"""
        <div class="rm-header">
            <span class="rm-brand">RepoMind</span>
            <span class="rm-repo-status">
                <code>{html.escape(repo_name)}</code>
                <span class="{dot_class}"></span>
                <span>{html.escape(label)}</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Repository panel
# ---------------------------------------------------------------------------


def render_repository_panel(
    initial_path: str,
    summary: dict[str, str] | None,
    advanced: dict[str, str],
    status: str,
    error: str | None = None,
) -> tuple[str, bool]:
    """Render the repository panel.

    Returns (path_from_input, index_clicked). Indexing itself is
    orchestrated by app.py; this component only renders state.
    """
    st.markdown(
        '<div class="rm-section-title">Repository</div>', unsafe_allow_html=True
    )

    st.markdown('<div class="rm-label">Path</div>', unsafe_allow_html=True)
    path = st.text_input(
        "Repository path",
        value=initial_path,
        placeholder=r"C:\path\to\repository",
        label_visibility="collapsed",
        key="repository_path_input",
    )
    st.markdown(
        '<div class="rm-caption">Local .py / .md repository path.</div>',
        unsafe_allow_html=True,
    )

    clicked = st.button("Index repository", type="primary", width="stretch")

    if error:
        st.markdown(
            f'<div class="rm-error">{html.escape(error)}</div>',
            unsafe_allow_html=True,
        )

    if summary:
        _render_meta(summary)

    with st.expander("Advanced"):
        _render_meta(advanced)

    return path, clicked


def _render_meta(items: dict[str, str]) -> None:
    rows = "".join(
        '<div class="rm-meta-row">'
        f'<span class="rm-meta-label">{html.escape(k)}</span>'
        f'<span class="rm-meta-value">{html.escape(v)}</span>'
        "</div>"
        for k, v in items.items()
    )
    st.markdown(f'<div class="rm-meta">{rows}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Chat workspace
# ---------------------------------------------------------------------------


def render_chat(
    messages: list[dict],
    index_status: str,
) -> tuple[bool, int | None, int | None, str | None]:
    """Render the Chat workspace.

    Returns (clear_clicked, selected_message_index, selected_source_index,
    followup_question).
    """

    title_col, clear_col = st.columns(
        [0.7, 0.3], gap="medium", vertical_alignment="center"
    )
    with title_col:
        st.markdown(
            '<div class="rm-section-title">Chat</div>', unsafe_allow_html=True
        )
    with clear_col:
        clear_clicked = st.button(
            "Clear conversation",
            key="clear_conversation",
            disabled=(not messages or index_status != "indexed"),
            width="stretch",
        )

    if index_status != "indexed":
        st.markdown(
            '<div class="rm-muted">Index a repository to start asking questions.</div>',
            unsafe_allow_html=True,
        )
        return clear_clicked, None, None, None

    if not messages:
        render_empty_state()
        return clear_clicked, None, None, None

    clicked_message = None
    clicked_source = None
    followup_question = None

    for message_index, message in enumerate(messages):
        role = message.get("role")
        body = _render_body(message.get("content", ""))
        if role == "user":
            st.markdown(
                '<div class="rm-msg rm-msg-user">'
                '<div class="rm-msg-label">You</div>'
                f'<div class="rm-msg-body">{body}</div>'
                "</div>",
                unsafe_allow_html=True,
            )
            continue

        # assistant message
        if message.get("refusal"):
            render_refusal_state()
            st.markdown(message.get("content", ""))
        elif message.get("error"):
            st.markdown(
                '<div class="rm-msg">'
                '<div class="rm-msg-label">RepoMind</div>'
                f'<div class="rm-msg-body rm-msg-body-error">{body}</div>'
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="rm-msg-label">RepoMind</div>', unsafe_allow_html=True)
            st.markdown(message.get("content", ""))

        # Source selector: "Source N" matches [Source N] in the answer.
        sources = message.get("sources", [])
        if sources:
            source_cols = st.columns(len(sources))
            for source_index, source_col in enumerate(source_cols):
                with source_col:
                    if st.button(
                        f"Source {source_index + 1}",
                        key=f"src_{message_index}_{source_index}",
                        width="stretch",
                    ):
                        clicked_message = message_index
                        clicked_source = source_index

        followups = message.get("followups", [])
        if followups:
            followup_cols = st.columns(len(followups))
            for followup_index, followup_col in enumerate(followup_cols):
                with followup_col:
                    if st.button(
                        followups[followup_index],
                        key=f"followup_{message_index}_{followup_index}",
                        width="stretch",
                    ):
                        followup_question = followups[followup_index]

    return clear_clicked, clicked_message, clicked_source, followup_question


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="rm-empty">
            <div class="rm-empty-title">Ask anything about this repository.</div>
            <div class="rm-muted">Try:</div>
            <ul>
                <li>How is self-attention implemented?</li>
                <li>Where is the training loop?</li>
                <li>How are pretrained weights loaded?</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Source inspector
# ---------------------------------------------------------------------------


def render_source_inspector(
    messages: list[dict],
    selected_message_index: int | None,
    selected_source_index: int | None = None,
) -> None:
    st.markdown('<div class="rm-section-title">Sources</div>', unsafe_allow_html=True)

    selected = None
    question = None
    if selected_message_index is not None and 0 <= selected_message_index < len(
        messages
    ):
        selected = messages[selected_message_index]
        # The user question that precedes this assistant answer.
        for candidate in reversed(messages[: selected_message_index + 1]):
            if candidate.get("role") == "user":
                question = candidate.get("content", "")
                break

    if selected is None or not selected.get("sources"):
        st.markdown(
            '<div class="rm-muted">No sources for this message.</div>',
            unsafe_allow_html=True,
        )
        return

    if question:
        st.markdown(
            f'<div class="rm-caption">For: {html.escape(question)}</div>',
            unsafe_allow_html=True,
        )

    for index, result in enumerate(selected["sources"], start=1):
        render_source_item(
            result,
            source_number=index,
            selected=(index - 1 == selected_source_index),
        )

    render_retrieval_debug(selected["sources"])


def render_source_item(
    result: dict,
    source_number: int | None = None,
    selected: bool = False,
) -> None:
    metadata = result.get("metadata", {})
    path = metadata.get("path", "N/A")
    qualified_name = metadata.get("qualified_name")
    source_role = metadata.get("source_role")
    relevance_reason = metadata.get("relevance_reason")
    symbol_type = metadata.get("symbol_type") or "chunk"
    start_line = metadata.get("start_line", "?")
    end_line = metadata.get("end_line", "?")
    language = "markdown" if str(path).endswith(".md") else "python"

    number_html = ""
    if source_number is not None:
        number_html = f'<div class="rm-source-number">Source {source_number}</div>'

    symbol_html = ""
    if qualified_name:
        symbol_html = (
            f'<div class="rm-source-symbol">{html.escape(qualified_name)}</div>'
        )

    role_html = ""
    if source_role:
        role_html = (
            f'<div class="rm-source-meta">Role: {html.escape(str(source_role))}</div>'
        )

    reason_html = ""
    if relevance_reason:
        reason_html = (
            '<div class="rm-caption">'
            f'{html.escape(str(relevance_reason))}'
            "</div>"
        )

    css_class = "rm-source rm-source-selected" if selected else "rm-source"

    st.markdown(
        f'<div class="{css_class}">'
        f"{number_html}"
        f'<div class="rm-source-file">{html.escape(path)}</div>'
        f"{symbol_html}"
        f"{role_html}"
        f'<div class="rm-source-meta">'
        f'{html.escape(symbol_type)} · lines {start_line}–{end_line}'
        "</div></div>",
        unsafe_allow_html=True,
    )
    if reason_html:
        st.markdown(reason_html, unsafe_allow_html=True)
    with st.expander("View source", expanded=selected):
        st.code(result.get("document", ""), language=language)


# ---------------------------------------------------------------------------
# Retrieval debug
# ---------------------------------------------------------------------------


def render_retrieval_debug(results: list[dict]) -> None:
    with st.expander("Retrieval details"):
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            groups = [
                [("Final Rank", str(index))],
                [
                    ("Vector Rank", _fmt(result.get("vector_rank"))),
                    ("Vector Similarity", _fmt(result.get("similarity"))),
                ],
                [
                    ("BM25 Rank", _fmt(result.get("bm25_rank"))),
                    ("BM25 Score", _fmt(result.get("bm25_score"))),
                ],
                [
                    ("RRF Rank", _fmt(result.get("rrf_rank"))),
                    ("RRF Score", _fmt(result.get("rrf_score"))),
                ],
                [
                    (
                        "Chunk Strategy",
                        str(metadata.get("chunk_strategy") or "N/A"),
                    ),
                    (
                        "Symbol",
                        str(metadata.get("qualified_name") or "N/A"),
                    ),
                    (
                        "Lines",
                        f'{metadata.get("start_line", "?")}'
                        f'–{metadata.get("end_line", "?")}',
                    ),
                ],
            ]
            blocks = []
            for group in groups:
                rows = "".join(
                    '<div class="rm-debug-row">'
                    f'<span class="rm-debug-label">{html.escape(label)}</span>'
                    f'<span class="rm-debug-value">{html.escape(value)}</span>'
                    "</div>"
                    for label, value in group
                )
                blocks.append(f'<div class="rm-debug-group">{rows}</div>')
            st.markdown(
                f'<div class="rm-debug-result">{"".join(blocks)}</div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Refusal state
# ---------------------------------------------------------------------------


def render_refusal_state() -> None:
    st.markdown(
        """
        <div class="rm-refusal">
            <div class="rm-refusal-title">Insufficient repository context</div>
            <div class="rm-refusal-body">
                The retrieved repository context does not contain enough
                information to answer this question reliably.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
