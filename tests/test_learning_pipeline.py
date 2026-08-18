import pytest

from learning import finalize_learning_map, prepare_learning_map_artifacts
from learning.schemas import FileProfile, LearningMap, SourceRef


def _doc(path):
    suffix = ".md" if path.lower().endswith(".md") else ".py"
    return {
        "content": "document",
        "metadata": {
            "path": path,
            "extension": suffix,
            "language": "markdown" if suffix == ".md" else "python",
        },
    }


def _chunk(path, symbol_name="", qualified_name="", start_line=1, end_line=10):
    return {
        "content": "chunk",
        "metadata": {
            "path": path,
            "start_line": start_line,
            "end_line": end_line,
            "symbol_name": symbol_name,
            "qualified_name": qualified_name,
        },
    }


def _inputs():
    documents = [
        _doc("README.md"),
        _doc("app.py"),
        _doc("model.py"),
    ]
    chunks = [
        _chunk("model.py", "forward", "Model.forward", 10, 40),
        _chunk("README.md", "", "", 1, 20),
        _chunk("app.py", "main", "main", 5, 30),
    ]
    return documents, chunks


def test_prepare_learning_map_artifacts_returns_complete_structure():
    documents, chunks = _inputs()

    artifacts = prepare_learning_map_artifacts(documents, chunks, top_k=3)

    assert list(artifacts.keys()) == [
        "file_profiles",
        "project_profile",
        "sources",
        "prompt",
    ]
    assert artifacts["file_profiles"]
    assert all(isinstance(item, FileProfile) for item in artifacts["file_profiles"])
    assert artifacts["project_profile"]["recommended_reading_order"]
    assert artifacts["sources"]
    assert all(isinstance(item, SourceRef) for item in artifacts["sources"])
    assert artifacts["prompt"]


def test_prepare_prompt_contains_required_learning_map_sections():
    documents, chunks = _inputs()

    prompt = prepare_learning_map_artifacts(documents, chunks)["prompt"]

    for heading in [
        "## What This Project Does",
        "## Where To Start",
        "## Main Modules",
        "## Core Flow",
        "## Recommended Reading Order",
        "## Starter Questions",
        "## Confidence Notes",
    ]:
        assert heading in prompt


def test_prepare_source_order_is_stable():
    documents, chunks = _inputs()

    first = prepare_learning_map_artifacts(documents, chunks, top_k=3)
    second = prepare_learning_map_artifacts(documents, chunks, top_k=3)

    assert first["sources"] == second["sources"]
    assert [source.path for source in first["sources"]] == [
        "README.md",
        "app.py",
        "model.py",
    ]


def test_finalize_learning_map_returns_learning_map():
    sources = [SourceRef(source_id=1, path="README.md", start_line=1, end_line=20)]
    markdown = """
## What This Project Does
It explains a repository [Source 1].

## Starter Questions
- What is the entry point?
- Where is retrieval?
- How are answers grounded?

## Confidence Notes
- Evidence is intentionally small.
"""

    result = finalize_learning_map(markdown, sources)

    assert isinstance(result, LearningMap)
    assert result.sources == sources
    assert result.starter_questions == [
        "What is the entry point?",
        "Where is retrieval?",
        "How are answers grounded?",
    ]


def test_prepare_rejects_empty_or_bad_inputs():
    documents, chunks = _inputs()

    with pytest.raises(ValueError, match="documents must not be empty"):
        prepare_learning_map_artifacts([], chunks)

    with pytest.raises(ValueError, match="chunks must not be empty"):
        prepare_learning_map_artifacts(documents, [])

    with pytest.raises(TypeError, match="documents must be a list"):
        prepare_learning_map_artifacts(tuple(documents), chunks)

    with pytest.raises(ValueError, match="metadata.path is required"):
        prepare_learning_map_artifacts(
            [{"content": "x", "metadata": {"path": ""}}],
            chunks,
        )


def test_finalize_rejects_bad_inputs():
    with pytest.raises(TypeError, match="markdown_text must be a string"):
        finalize_learning_map(None, [])

    with pytest.raises(ValueError, match="sources must not be None"):
        finalize_learning_map("", None)
