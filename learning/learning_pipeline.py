"""Pure orchestration helpers for Learning Map preparation."""

from __future__ import annotations

from learning.learning_map import (
    build_learning_map_prompt,
    build_learning_map_result,
    select_learning_map_sources,
)
from learning.learning_metadata import build_file_profiles
from learning.project_analyzer import build_project_profile
from learning.schemas import LearningMap


def prepare_learning_map_artifacts(
    documents,
    chunks,
    user_language="Chinese",
    top_k=8,
) -> dict:
    """Prepare all offline artifacts needed before a Learning Map LLM call."""

    _validate_records("documents", documents)
    _validate_records("chunks", chunks)
    if not isinstance(user_language, str) or not user_language.strip():
        raise ValueError("user_language must be a non-empty string.")
    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer.")

    file_profiles = build_file_profiles(documents, chunks)
    project_profile = build_project_profile(file_profiles, documents, chunks)
    sources = select_learning_map_sources(file_profiles, chunks, top_k=top_k)
    prompt = build_learning_map_prompt(
        project_profile=project_profile,
        sources=sources,
        user_language=user_language,
    )

    return {
        "file_profiles": file_profiles,
        "project_profile": project_profile,
        "sources": sources,
        "prompt": prompt,
    }


def finalize_learning_map(markdown_text, sources) -> LearningMap:
    """Create a LearningMap object from generated Markdown and selected sources."""

    if not isinstance(markdown_text, str):
        raise TypeError("markdown_text must be a string.")
    if sources is None:
        raise ValueError("sources must not be None.")
    return build_learning_map_result(markdown_text, sources)


def _validate_records(name: str, records) -> None:
    if not isinstance(records, list):
        raise TypeError(f"{name} must be a list.")
    if not records:
        raise ValueError(f"{name} must not be empty.")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise TypeError(f"{name}[{index}] must be a dict.")

        metadata = record.get("metadata")
        if not isinstance(metadata, dict):
            raise ValueError(f"{name}[{index}] must include metadata dict.")

        if not str(metadata.get("path") or "").strip():
            raise ValueError(f"{name}[{index}] metadata.path is required.")
