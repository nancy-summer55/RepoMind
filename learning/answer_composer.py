"""Prompt builders for guided repository answers."""

from __future__ import annotations

from learning.schemas import SourceRef


SUPPORTED_INTENTS = {
    "project_overview",
    "feature_implementation",
    "ai_concept",
    "file_or_symbol",
    "configuration",
    "unsupported",
}

GROUNDING_RULES = """Grounding rules:
- Repository facts may only come from the provided sources.
- Every repository fact must cite sources with [Source N].
- Do not invent files, classes, functions, configuration values, or runtime behavior.
- If the evidence is insufficient, say so clearly."""


def build_answer_sources_context(sources: list[dict] | list[SourceRef]) -> str:
    """Render sources into a stable [Source N] context block."""

    if not sources:
        raise ValueError("sources must not be empty.")

    parts = []
    for index, source in enumerate(sources, start=1):
        ref = _source_ref(source, index)
        lines = [
            f"[Source {index}]",
            f"File: {ref.path}",
            f"Lines: {ref.start_line}-{ref.end_line}",
        ]
        if ref.qualified_name:
            lines.append(f"Qualified Name: {ref.qualified_name}")
        if ref.symbol_name:
            lines.append(f"Symbol: {ref.symbol_name}")
        if ref.source_role:
            lines.append(f"Source Role: {ref.source_role}")

        document = _source_document(source)
        if document:
            lines.extend(["", document])

        parts.append("\n".join(lines))

    return "\n\n".join(parts)


def build_feature_answer_prompt(question, sources, user_language="Chinese") -> str:
    return _build_prompt(
        question=question,
        sources=sources,
        user_language=user_language,
        task="Explain how this feature or workflow is implemented in the repository.",
        sections=[
            "## Conclusion",
            "## Related Files",
            "## Implementation Flow",
            "## Key Functions",
            "## Source Evidence",
            "## Next Questions",
        ],
    )


def build_concept_answer_prompt(question, sources, user_language="Chinese") -> str:
    return _build_prompt(
        question=question,
        sources=sources,
        user_language=user_language,
        task="Explain the concept using only how it appears in this repository.",
        sections=[
            "## Concept",
            "## Where It Appears",
            "## Repository Implementation",
            "## Inputs And Outputs",
            "## Why It Matters",
            "## Source Evidence",
            "## Next Questions",
        ],
    )


def build_overview_answer_prompt(question, sources, user_language="Chinese") -> str:
    return _build_prompt(
        question=question,
        sources=sources,
        user_language=user_language,
        task="Give a grounded project overview and orient the reader.",
        sections=[
            "## Summary",
            "## Entry Points",
            "## Main Files",
            "## Architecture Notes",
            "## Source Evidence",
            "## Next Questions",
        ],
    )


def build_configuration_answer_prompt(question, sources, user_language="Chinese") -> str:
    return _build_prompt(
        question=question,
        sources=sources,
        user_language=user_language,
        task="Explain configuration, defaults, environment values, and runtime setup.",
        sections=[
            "## Configuration Summary",
            "## Where Values Are Defined",
            "## Runtime Overrides",
            "## Operational Impact",
            "## Source Evidence",
            "## Next Questions",
        ],
    )


def build_refusal_prompt(question, sources, user_language="Chinese") -> str:
    return _build_prompt(
        question=question,
        sources=sources,
        user_language=user_language,
        task="Explain that the available repository evidence is insufficient.",
        sections=[
            "## Unable To Answer",
            "## Available Evidence",
            "## Missing Evidence",
            "## Source Evidence",
            "## Next Questions",
        ],
    )


def build_answer_prompt(question, intent, sources, user_language="Chinese") -> str:
    """Dispatch to an intent-specific answer prompt builder."""

    _validate_question(question)
    if intent not in SUPPORTED_INTENTS:
        raise ValueError(f"Unknown intent: {intent}")

    if intent == "feature_implementation":
        return build_feature_answer_prompt(question, sources, user_language)
    if intent == "ai_concept":
        return build_concept_answer_prompt(question, sources, user_language)
    if intent == "project_overview":
        return build_overview_answer_prompt(question, sources, user_language)
    if intent == "configuration":
        return build_configuration_answer_prompt(question, sources, user_language)
    if intent == "file_or_symbol":
        return _build_prompt(
            question=question,
            sources=sources,
            user_language=user_language,
            task="Explain the named file or symbol using exact source evidence.",
            sections=[
                "## Summary",
                "## Definition",
                "## Responsibilities",
                "## Source Evidence",
                "## Next Questions",
            ],
        )
    return build_refusal_prompt(question, sources, user_language)


def _build_prompt(question, sources, user_language, task, sections) -> str:
    _validate_question(question)
    if not isinstance(user_language, str) or not user_language.strip():
        raise ValueError("user_language must be a non-empty string.")

    section_text = "\n".join(sections)
    context = build_answer_sources_context(sources)

    return f"""You are RepoMind, a repository learning assistant.

Write the answer in {user_language}.

Task:
{task}

Use this exact Markdown structure:

{section_text}

{GROUNDING_RULES}

Question:
{question.strip()}

Sources:

{context}
"""


def _validate_question(question) -> None:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string.")


def _source_ref(source, fallback_id: int) -> SourceRef:
    if isinstance(source, SourceRef):
        return SourceRef(
            source_id=source.source_id or fallback_id,
            path=source.path,
            start_line=source.start_line,
            end_line=source.end_line,
            symbol_name=source.symbol_name,
            qualified_name=source.qualified_name,
            source_role=source.source_role,
            relevance_reason=source.relevance_reason,
        )

    if not isinstance(source, dict):
        raise TypeError("sources must contain dict or SourceRef items.")

    metadata = source.get("metadata", source)
    return SourceRef(
        source_id=int(source.get("source_id") or fallback_id),
        path=str(metadata.get("path") or ""),
        start_line=int(metadata.get("start_line") or 0),
        end_line=int(metadata.get("end_line") or 0),
        symbol_name=str(metadata.get("symbol_name") or ""),
        qualified_name=str(metadata.get("qualified_name") or ""),
        source_role=str(metadata.get("source_role") or source.get("source_role") or ""),
        relevance_reason=str(
            metadata.get("relevance_reason") or source.get("relevance_reason") or ""
        ),
    )


def _source_document(source) -> str:
    if isinstance(source, dict):
        return str(source.get("document") or source.get("content") or "").strip()
    return ""
