"""Bridge repository loading/chunking to Learning artifacts."""

from __future__ import annotations

from pathlib import Path

from ast_chunker import split_documents_ast
from chunker import split_documents
from learning.learning_pipeline import prepare_learning_map_artifacts
from repo_loader import load_repository


def load_and_chunk_repository(
    repo_path,
    chunk_size=1200,
    chunk_overlap=200,
    chunk_strategy="ast",
) -> tuple[list[dict], list[dict]]:
    """Load a repository and split it into chunks for Learning preparation."""

    _validate_repo_path(repo_path)
    _validate_chunk_settings(chunk_size, chunk_overlap)

    documents = load_repository(repo_path)
    if not documents:
        raise ValueError("No supported .py or .md files were found.")

    if chunk_strategy == "ast":
        chunks = split_documents_ast(
            documents=documents,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    else:
        chunks = split_documents(
            documents=documents,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    if not chunks:
        raise ValueError("No chunks were created from the repository.")

    return documents, chunks


def build_repository_learning_artifacts(
    repo_path,
    chunk_size=1200,
    chunk_overlap=200,
    chunk_strategy="ast",
    user_language="Chinese",
    top_k=8,
) -> dict:
    """Build offline Learning artifacts from a repository path."""

    documents, chunks = load_and_chunk_repository(
        repo_path=repo_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunk_strategy=chunk_strategy,
    )
    artifacts = prepare_learning_map_artifacts(
        documents=documents,
        chunks=chunks,
        user_language=user_language,
        top_k=top_k,
    )

    return {
        "documents": documents,
        "chunks": chunks,
        "file_profiles": artifacts["file_profiles"],
        "project_profile": artifacts["project_profile"],
        "sources": artifacts["sources"],
        "prompt": artifacts["prompt"],
    }


def _validate_repo_path(repo_path) -> None:
    if repo_path is None:
        raise ValueError("repo_path is required.")

    path = Path(repo_path).expanduser()
    if not path.exists():
        raise ValueError(f"Repository does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Repository path is not a directory: {path}")


def _validate_chunk_settings(chunk_size, chunk_overlap) -> None:
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
        raise ValueError("chunk_overlap must be a non-negative integer.")
