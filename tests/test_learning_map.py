from learning import (
    build_file_profiles,
    build_learning_map_prompt,
    build_learning_map_result,
    build_project_profile,
    select_learning_map_sources,
)
from learning.schemas import LearningMap


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


def _fixtures():
    documents = [
        _doc("README.md"),
        _doc("docs/guide.md"),
        _doc("app.py"),
        _doc("model.py"),
        _doc("utils/helpers.py"),
    ]
    chunks = [
        _chunk("utils/helpers.py", "format_name", "format_name", 1, 8),
        _chunk("model.py", "forward", "Model.forward", 10, 40),
        _chunk("README.md", "", "", 1, 20),
        _chunk("README.md", "", "", 1, 20),
        _chunk("docs/guide.md", "", "", 3, 18),
        _chunk("app.py", "main", "main", 5, 30),
    ]
    file_profiles = build_file_profiles(documents, chunks)
    project_profile = build_project_profile(file_profiles, documents, chunks)
    return documents, chunks, file_profiles, project_profile


def test_select_sources_prioritizes_docs_entry_and_important_files():
    _, chunks, file_profiles, _ = _fixtures()

    sources = select_learning_map_sources(file_profiles, chunks, top_k=4)

    assert [source.path for source in sources] == [
        "README.md",
        "docs/guide.md",
        "app.py",
        "model.py",
    ]
    assert sources[2].qualified_name == "main"
    assert sources[3].qualified_name == "Model.forward"


def test_select_sources_is_stable_and_deduplicated():
    _, chunks, file_profiles, _ = _fixtures()

    first = select_learning_map_sources(file_profiles, chunks, top_k=8)
    second = select_learning_map_sources(file_profiles, chunks, top_k=8)

    assert first == second
    assert len(
        {
            (source.path, source.start_line, source.end_line)
            for source in first
        }
    ) == len(first)
    assert [source.source_id for source in first] == [1, 2, 3, 4, 5]


def test_prompt_contains_required_sections_rules_and_sources():
    _, chunks, file_profiles, project_profile = _fixtures()
    sources = select_learning_map_sources(file_profiles, chunks, top_k=4)

    prompt = build_learning_map_prompt(project_profile, sources)

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

    assert "Repository facts may only come from the selected sources" in prompt
    assert "Every repository fact must cite sources with [Source N]" in prompt
    assert "Do not invent files, functions, classes" in prompt
    assert "Generate exactly 3 starter questions" in prompt
    assert "[Source 1]" in prompt
    assert "File: README.md" in prompt
    assert "Write the answer in Chinese" in prompt


def test_build_learning_map_result_wraps_stable_fields():
    _, chunks, file_profiles, _ = _fixtures()
    sources = select_learning_map_sources(file_profiles, chunks, top_k=2)
    markdown = """
## What This Project Does
RepoMind explains repositories using selected evidence [Source 1].

## Starter Questions
1. How does indexing start?
2. Where are chunks created?
3. How are sources cited?

## Confidence Notes
- Evidence is limited to selected chunks.
- No call graph was built.
"""

    result = build_learning_map_result(markdown, sources)

    assert isinstance(result, LearningMap)
    assert result.project_summary == (
        "RepoMind explains repositories using selected evidence [Source 1]."
    )
    assert result.starter_questions == [
        "How does indexing start?",
        "Where are chunks created?",
        "How are sources cited?",
    ]
    assert result.confidence_notes == [
        "Evidence is limited to selected chunks.",
        "No call graph was built.",
    ]
    assert result.sources == sources
    assert result.main_modules == []
