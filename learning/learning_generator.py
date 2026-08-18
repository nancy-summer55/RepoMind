"""Injectable Learning Map generation helpers."""

from __future__ import annotations

from learning.indexing_bridge import build_repository_learning_artifacts
from learning.learning_pipeline import finalize_learning_map
from learning.schemas import LearningMap


def generate_learning_map_markdown(prompt, llm_callable) -> str:
    """Generate Learning Map Markdown through an injected callable."""

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string.")
    if not callable(llm_callable):
        raise TypeError("llm_callable must be callable.")

    markdown = llm_callable(prompt)
    if not isinstance(markdown, str):
        raise TypeError("llm_callable must return a string.")
    if not markdown.strip():
        raise ValueError("llm_callable returned empty markdown.")

    return markdown


def generate_learning_map_from_artifacts(
    project_profile,
    sources,
    prompt,
    llm_callable,
) -> LearningMap:
    """Generate and wrap a LearningMap from prepared offline artifacts."""

    markdown = generate_learning_map_markdown(prompt, llm_callable)
    return finalize_learning_map(markdown, sources)


def generate_repository_learning_map(
    repo_path,
    llm_callable,
    chunk_size=1200,
    chunk_overlap=200,
    chunk_strategy="ast",
    user_language="Chinese",
    top_k=8,
) -> dict:
    """Build repository artifacts and generate a LearningMap."""

    artifacts = build_repository_learning_artifacts(
        repo_path=repo_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunk_strategy=chunk_strategy,
        user_language=user_language,
        top_k=top_k,
    )
    markdown = generate_learning_map_markdown(
        artifacts["prompt"],
        llm_callable,
    )
    learning_map = finalize_learning_map(
        markdown,
        artifacts["sources"],
    )

    return {
        "documents": artifacts["documents"],
        "chunks": artifacts["chunks"],
        "file_profiles": artifacts["file_profiles"],
        "project_profile": artifacts["project_profile"],
        "sources": artifacts["sources"],
        "prompt": artifacts["prompt"],
        "learning_map": learning_map,
        "markdown": markdown,
    }
