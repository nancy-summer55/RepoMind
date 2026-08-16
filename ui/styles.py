"""All custom CSS for the RepoMind UI lives here.

Keep this file the single home for custom styling. Selectors are limited
to stable data-testid attributes and the .rm-* classes used by
components.py.
"""

import streamlit as st


def apply_styles() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


_CSS = """
<style>
/* ---------- page background & typography ---------- */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #F8F9FB;
    color: #17181A;
}
[data-testid="stHeader"] {
    background: transparent;
}
[data-testid="stAppViewContainer"] {
    font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
    font-size: 14px;
}

/* ---------- header ---------- */
.rm-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 2px 2px 16px 2px;
    margin-bottom: 20px;
    border-bottom: 1px solid #E4E7EB;
}
.rm-brand {
    font-size: 22px;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: #17181A;
}
.rm-repo-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #5F6368;
}
.rm-repo-status code {
    font-family: "JetBrains Mono", SFMono-Regular, Consolas, monospace;
    font-size: 13px;
    color: #17181A;
    background: #F3F4F6;
    border: 1px solid #E4E7EB;
    border-radius: 6px;
    padding: 2px 8px;
}
.rm-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #2F7D4A;
    display: inline-block;
}

/* ---------- panels ---------- */
[data-testid="stColumn"] {
    background-color: #FFFFFF;
    border: 1px solid #E4E7EB;
    border-radius: 10px;
    padding: 18px 20px;
}

/* ---------- section titles & labels ---------- */
.rm-section-title {
    font-size: 15px;
    font-weight: 600;
    color: #17181A;
    margin: 0 0 14px 0;
}
.rm-label {
    font-size: 12px;
    color: #8B9098;
    margin-bottom: 6px;
}
.rm-caption {
    font-size: 12px;
    color: #8B9098;
    margin: 6px 0 0 0;
}
.rm-muted {
    color: #8B9098;
}

/* ---------- repository path ---------- */
.rm-path {
    font-family: "JetBrains Mono", SFMono-Regular, Consolas, monospace;
    font-size: 12.5px;
    color: #5F6368;
    background: #F6F7F9;
    border: 1px solid #E4E7EB;
    border-radius: 8px;
    padding: 8px 10px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ---------- buttons ---------- */
[data-testid="stBaseButton-primary"] {
    background-color: #4F46E5;
    border: 1px solid #4F46E5;
    border-radius: 8px;
    font-weight: 500;
}
[data-testid="stBaseButton-primary"]:hover {
    background-color: #4338CA;
    border-color: #4338CA;
}
[data-testid="stBaseButton-secondary"] {
    border-radius: 8px;
}
[data-testid="stBaseButton-header"] {
    display: none;
}

/* ---------- metadata list ---------- */
.rm-meta {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 6px 16px;
    font-size: 13px;
    margin: 18px 0 0 0;
}
.rm-meta-label {
    color: #5F6368;
}
.rm-meta-value {
    font-family: "JetBrains Mono", SFMono-Regular, Consolas, monospace;
    color: #17181A;
    text-align: right;
}

/* ---------- chat ---------- */
.rm-msg {
    margin-bottom: 22px;
}
.rm-msg-label {
    font-size: 12px;
    font-weight: 600;
    color: #8B9098;
    margin-bottom: 6px;
}
.rm-msg-body {
    font-size: 15px;
    line-height: 1.6;
    color: #17181A;
    max-width: 760px;
}
.rm-msg-body code {
    font-family: "JetBrains Mono", SFMono-Regular, Consolas, monospace;
    font-size: 13px;
    background: #EEF2FF;
    border-radius: 4px;
    padding: 1px 5px;
    color: #4F46E5;
}
.rm-msg-user .rm-msg-body {
    background: #F3F4F6;
    border-radius: 8px;
    padding: 10px 14px;
}
.rm-citations {
    display: flex;
    gap: 8px;
    margin-top: 10px;
}
.rm-citation {
    font-family: "JetBrains Mono", SFMono-Regular, Consolas, monospace;
    font-size: 12px;
    color: #4F46E5;
    background: #EEF2FF;
    border: 1px solid #C7D2FE;
    border-radius: 8px;
    padding: 2px 10px;
}

/* ---------- source item ---------- */
.rm-source {
    border: 1px solid #E4E7EB;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 12px;
}
.rm-source-file {
    font-family: "JetBrains Mono", SFMono-Regular, Consolas, monospace;
    font-size: 13px;
    font-weight: 600;
    color: #17181A;
}
.rm-source-symbol {
    font-family: "JetBrains Mono", SFMono-Regular, Consolas, monospace;
    font-size: 13px;
    color: #5F6368;
    margin-top: 4px;
}
.rm-source-meta {
    font-size: 12px;
    color: #8B9098;
    margin-top: 4px;
}

/* ---------- retrieval debug ---------- */
.rm-debug {
    font-size: 13px;
}
.rm-debug-group {
    margin-bottom: 10px;
}
.rm-debug-group:last-child {
    margin-bottom: 0;
}
.rm-debug-row {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    padding: 2px 0;
}
.rm-debug-label {
    color: #5F6368;
}
.rm-debug-value {
    font-family: "JetBrains Mono", SFMono-Regular, Consolas, monospace;
    color: #17181A;
    text-align: right;
}

/* ---------- refusal state ---------- */
.rm-refusal {
    background: #EEF2FF;
    border: 1px solid #C7D2FE;
    border-radius: 10px;
    padding: 14px 16px;
}
.rm-refusal-title {
    font-size: 14px;
    font-weight: 600;
    color: #17181A;
    margin-bottom: 4px;
}
.rm-refusal-body {
    font-size: 13px;
    line-height: 1.55;
    color: #5F6368;
}

/* ---------- empty state ---------- */
.rm-empty {
    padding: 24px 4px;
    color: #5F6368;
}
.rm-empty-title {
    font-size: 15px;
    font-weight: 600;
    color: #17181A;
    margin-bottom: 8px;
}
.rm-empty ul {
    margin: 8px 0 0 0;
    padding-left: 18px;
}
.rm-empty li {
    margin: 4px 0;
}

/* ---------- backend notice ---------- */
.rm-notice {
    font-size: 12px;
    color: #8B9098;
    margin: 4px 0 0 0;
}

/* ---------- code blocks ---------- */
[data-testid="stCode"] pre {
    background: #F6F7F9;
    font-family: "JetBrains Mono", SFMono-Regular, Consolas, monospace;
    font-size: 12.5px;
    line-height: 1.5;
}

/* ---------- chat input ---------- */
[data-testid="stChatInput"] {
    background: #FFFFFF;
    border: 1px solid #E4E7EB;
    border-radius: 10px;
}

/* ---------- expanders ---------- */
[data-testid="stExpander"] {
    border: 1px solid #E4E7EB;
    border-radius: 8px;
    background: #FFFFFF;
}
</style>
"""