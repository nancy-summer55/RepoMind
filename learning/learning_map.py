"""Learning Map source selection and prompt/result helpers."""

from __future__ import annotations

from pathlib import PurePosixPath

from learning.schemas import LearningMap, SourceRef


KEY_SYMBOLS = {
    "train",
    "forward",
    "generate",
    "encode",
    "retrieve",
    "ask",
    "main",
}

REQUIRED_SECTIONS = [
    "## What This Project Does",
    "## Where To Start",
    "## Main Modules",
    "## Core Flow",
    "## Recommended Reading Order",
    "## Starter Questions",
    "## Confidence Notes",
]


def select_learning_map_sources(file_profiles, chunks, top_k=8) -> list[SourceRef]:
    """Select stable grounded sources for a future Learning Map request."""

    profile_by_path = {
        profile.path: profile
        for profile in file_profiles
    }
    ranked_chunks = sorted(
        chunks,
        key=lambda chunk: _chunk_rank_key(chunk, profile_by_path),
    )

    selected = []
    seen_ranges = set()
    per_file_counts = {}

    for chunk in ranked_chunks:
        metadata = chunk.get("metadata", {})
        path = str(metadata.get("path") or "")
        if not path:
            continue

        key = (
            path,
            int(metadata.get("start_line") or 0),
            int(metadata.get("end_line") or 0),
        )
        if key in seen_ranges:
            continue

        max_per_file = 2 if _has_key_symbol(metadata) else 1
        if per_file_counts.get(path, 0) >= max_per_file:
            continue

        selected.append(
            SourceRef(
                source_id=len(selected) + 1,
                path=path,
                start_line=int(metadata.get("start_line") or 0),
                end_line=int(metadata.get("end_line") or 0),
                symbol_name=str(metadata.get("symbol_name") or ""),
                qualified_name=str(metadata.get("qualified_name") or ""),
            )
        )
        seen_ranges.add(key)
        per_file_counts[path] = per_file_counts.get(path, 0) + 1

        if len(selected) >= top_k:
            break

    return selected


def build_learning_map_prompt(
    project_profile,
    sources,
    user_language="Chinese",
) -> str:
    """Build the Learning Map prompt without calling a model."""

    profile_text = _format_project_profile(project_profile)
    source_text = _format_sources(sources)
    sections = "\n".join(REQUIRED_SECTIONS)

    return f"""You are RepoMind's Learning Map writer.

Write the answer in {user_language}.

Use this exact Markdown structure:

{sections}

Grounding rules:
- Repository facts may only come from the selected sources below.
- Every repository fact must cite sources with [Source N].
- Do not invent files, functions, classes, configuration values, or runtime behavior.
- Generate exactly 3 starter questions.
- If evidence is insufficient, write that limitation in Confidence Notes.

Repository / project profile:

{profile_text}

Selected source context:

{source_text}
"""


def build_learning_map_result(markdown_text, sources) -> LearningMap:
    """Wrap generated Markdown into a stable LearningMap object."""

    sections = _parse_sections(markdown_text)
    return LearningMap(
        project_summary=sections.get("What This Project Does", "").strip(),
        starter_questions=_parse_list_items(
            sections.get("Starter Questions", "")
        )[:3],
        sources=list(sources),
        confidence_notes=_parse_list_items(
            sections.get("Confidence Notes", "")
        ),
    )


def _chunk_rank_key(chunk, profile_by_path: dict) -> tuple:
    metadata = chunk.get("metadata", {})
    path = str(metadata.get("path") or "")
    profile = profile_by_path.get(path)
    importance = profile.importance_score if profile else 0.0
    is_entry = bool(profile.is_entry_candidate) if profile else False
    category = profile.category if profile else ""

    return (
        _source_group(path, category, is_entry),
        -importance,
        0 if _has_key_symbol(metadata) else 1,
        path,
        int(metadata.get("start_line") or 0),
        int(metadata.get("end_line") or 0),
        str(metadata.get("qualified_name") or ""),
    )


def _source_group(path: str, category: str, is_entry: bool) -> int:
    lowered = path.lower()
    filename = PurePosixPath(lowered).name
    if filename == "readme.md":
        return 0
    if category == "doc" or lowered.startswith("docs/") or "/docs/" in lowered:
        return 1
    if is_entry:
        return 2
    return 3


def _has_key_symbol(metadata: dict) -> bool:
    values = [
        str(metadata.get("symbol_name") or ""),
        str(metadata.get("qualified_name") or ""),
    ]
    for value in values:
        for token in value.replace(".", "_").split("_"):
            if token.lower() in KEY_SYMBOLS:
                return True
    return False


def _format_project_profile(project_profile) -> str:
    if not project_profile:
        return "- No project profile provided."

    lines = []
    for key in [
        "repository_name",
        "summary_candidates",
        "entry_files",
        "main_modules",
        "key_concepts",
        "recommended_reading_order",
        "evidence_sources",
    ]:
        value = project_profile.get(key)
        lines.append(f"- {key}: {value!r}")
    return "\n".join(lines)


def _format_sources(sources) -> str:
    if not sources:
        return "No selected sources were available."

    parts = []
    for source in sources:
        symbol = source.qualified_name or source.symbol_name or "N/A"
        parts.append(
            "\n".join(
                [
                    f"[Source {source.source_id}]",
                    f"File: {source.path}",
                    f"Lines: {source.start_line}-{source.end_line}",
                    f"Symbol: {symbol}",
                ]
            )
        )
    return "\n\n".join(parts)


def _parse_sections(markdown_text: str) -> dict[str, str]:
    sections = {}
    current_title = None
    current_lines = []

    for line in str(markdown_text or "").splitlines():
        if line.startswith("## "):
            if current_title is not None:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = line[3:].strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)

    if current_title is not None:
        sections[current_title] = "\n".join(current_lines).strip()

    return sections


def _parse_list_items(section_text: str) -> list[str]:
    items = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
        elif len(stripped) > 3 and stripped[0].isdigit() and stripped[1:3] == ". ":
            items.append(stripped[3:].strip())
    return items
