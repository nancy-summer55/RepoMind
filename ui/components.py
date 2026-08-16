"""Reusable Streamlit UI components for RepoMind.

Pure UI: every function only renders the data it receives and never
touches the retrieval backend. Phase 1 renders mock data only.
"""

import html
import re

import streamlit as st

_INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def _render_body(text: str) -> str:
    """Escape HTML, then turn `code` spans into <code> tags."""
    escaped = html.escape(text)
    return _INLINE_CODE_RE.sub(r"<code>\1</code>", escaped)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------


def render_header(repo_name: str = "", status: str = "") -> None:
    st.markdown(
        f"""
        <div class="rm-header">
            <span class="rm-brand">RepoMind</span>
            <span class="rm-repo-status">
                <code>{html.escape(repo_name)}</code>
                <span class="rm-dot"></span>
                <span>{html.escape(status)}</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Repository panel
# ---------------------------------------------------------------------------


def render_repository_panel(
    path: str,
    summary: dict[str, str],
    advanced: dict[str, str],
    full_path: str | None = None,
) -> None:
    st.markdown(
        '<div class="rm-section-title">Repository</div>', unsafe_allow_html=True
    )

    st.markdown('<div class="rm-label">Path</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="rm-path" title="{html.escape(full_path or path)}">'
        f"{html.escape(path)}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="rm-caption">Full path shown on hover.</div>',
        unsafe_allow_html=True,
    )

    if st.button("Index repository", type="primary", width="stretch"):
        st.toast("Mock indexing only - backend not connected yet.")

    _render_meta(summary)

    with st.expander("Advanced"):
        _render_meta(advanced)


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


def render_mock_chat(messages: list[dict]) -> None:
    st.markdown('<div class="rm-section-title">Chat</div>', unsafe_allow_html=True)

    if not messages:
        render_empty_state()
        return

    for message in messages:
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
        else:
            citations = "".join(
                f'<span class="rm-citation">[{i}]</span>'
                for i in message.get("citations", [])
            )
            st.markdown(
                '<div class="rm-msg">'
                '<div class="rm-msg-label">RepoMind</div>'
                f'<div class="rm-msg-body">{body}</div>'
                f'<div class="rm-citations">{citations}</div>'
                "</div>",
                unsafe_allow_html=True,
            )


def render_backend_notice() -> None:
    st.markdown(
        '<div class="rm-notice">Backend connection will be added in Phase 3.</div>',
        unsafe_allow_html=True,
    )


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
    sources: list[dict],
    retrieval_debug: list[list[tuple[str, str]]] | None = None,
) -> None:
    st.markdown('<div class="rm-section-title">Sources</div>', unsafe_allow_html=True)

    if not sources:
        st.markdown(
            '<div class="rm-muted">No sources for this message.</div>',
            unsafe_allow_html=True,
        )
        return

    for source in sources:
        render_source_item(source)

    if retrieval_debug:
        render_retrieval_debug(retrieval_debug)


def render_source_item(source: dict) -> None:
    st.markdown(
        '<div class="rm-source">'
        f'<div class="rm-source-file">{html.escape(source["path"])}</div>'
        f'<div class="rm-source-symbol">{html.escape(source["qualified_name"])}</div>'
        f'<div class="rm-source-meta">'
        f'{html.escape(source["symbol_type"])} · '
        f'lines {source["start_line"]}–{source["end_line"]}'
        "</div></div>",
        unsafe_allow_html=True,
    )
    with st.expander("View source"):
        st.code(
            "def forward(self, x):\n"
            "    B, T, C = x.size()\n"
            "    ...\n",
            language="python",
        )


# ---------------------------------------------------------------------------
# Retrieval debug
# ---------------------------------------------------------------------------


def render_retrieval_debug(groups: list[list[tuple[str, str]]]) -> None:
    with st.expander("Retrieval details"):
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
            f'<div class="rm-debug">{"".join(blocks)}</div>',
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