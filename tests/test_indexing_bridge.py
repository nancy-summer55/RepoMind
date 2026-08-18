import pytest

from learning import (
    build_repository_learning_artifacts,
    load_and_chunk_repository,
)
from learning.schemas import FileProfile, SourceRef


def _write_minimal_repo(root):
    (root / "README.md").write_text(
        "# Demo\n\nThis repository demonstrates a small app.",
        encoding="utf-8",
    )
    (root / "app.py").write_text(
        "def main():\n"
        "    return 'hello'\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )
    (root / "model.py").write_text(
        "class Model:\n"
        "    def forward(self, value):\n"
        "        return value\n",
        encoding="utf-8",
    )


def test_load_and_chunk_repository_returns_documents_and_ast_chunks(tmp_path):
    _write_minimal_repo(tmp_path)

    documents, chunks = load_and_chunk_repository(tmp_path, chunk_strategy="ast")

    assert {document["metadata"]["path"] for document in documents} == {
        "README.md",
        "app.py",
        "model.py",
    }
    assert chunks
    assert any(
        chunk["metadata"].get("qualified_name") == "Model.forward"
        for chunk in chunks
    )


def test_load_and_chunk_repository_supports_fixed_chunking(tmp_path):
    _write_minimal_repo(tmp_path)

    documents, chunks = load_and_chunk_repository(tmp_path, chunk_strategy="fixed")

    assert len(documents) == 3
    assert chunks
    assert all("chunk_index" in chunk["metadata"] for chunk in chunks)


def test_build_repository_learning_artifacts_returns_complete_structure(tmp_path):
    _write_minimal_repo(tmp_path)

    artifacts = build_repository_learning_artifacts(
        tmp_path,
        chunk_strategy="ast",
        top_k=4,
    )

    assert list(artifacts.keys()) == [
        "documents",
        "chunks",
        "file_profiles",
        "project_profile",
        "sources",
        "prompt",
    ]
    assert artifacts["documents"]
    assert artifacts["chunks"]
    assert all(isinstance(item, FileProfile) for item in artifacts["file_profiles"])
    assert artifacts["project_profile"]["recommended_reading_order"][0] == "README.md"
    assert all(isinstance(item, SourceRef) for item in artifacts["sources"])
    assert "## What This Project Does" in artifacts["prompt"]


def test_empty_directory_raises_clear_error(tmp_path):
    with pytest.raises(ValueError, match="No supported .py or .md files"):
        load_and_chunk_repository(tmp_path)


def test_directory_without_supported_files_raises_clear_error(tmp_path):
    (tmp_path / "notes.txt").write_text("not indexed", encoding="utf-8")

    with pytest.raises(ValueError, match="No supported .py or .md files"):
        build_repository_learning_artifacts(tmp_path)


def test_bad_repository_path_raises_clear_error(tmp_path):
    missing = tmp_path / "missing"

    with pytest.raises(ValueError, match="Repository does not exist"):
        load_and_chunk_repository(missing)
