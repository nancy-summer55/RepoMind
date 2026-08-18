import pytest

from learning import (
    generate_learning_map_from_artifacts,
    generate_learning_map_markdown,
    generate_repository_learning_map,
)
from learning.schemas import LearningMap, SourceRef


VALID_MARKDOWN = """
## What This Project Does
This project demonstrates Learning Map generation [Source 1].

## Starter Questions
- What does the project do?
- Where should I start?
- Which files matter most?

## Confidence Notes
- This is generated from selected sources only.
"""


def _write_minimal_repo(root):
    (root / "README.md").write_text(
        "# Demo\n\nSmall repository.",
        encoding="utf-8",
    )
    (root / "app.py").write_text(
        "def main():\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )
    (root / "model.py").write_text(
        "class Model:\n"
        "    def forward(self, value):\n"
        "        return value\n",
        encoding="utf-8",
    )


def test_generate_learning_map_markdown_uses_injected_callable():
    calls = []

    def fake_llm(prompt):
        calls.append(prompt)
        return VALID_MARKDOWN

    result = generate_learning_map_markdown("prompt text", fake_llm)

    assert result == VALID_MARKDOWN
    assert calls == ["prompt text"]


def test_generate_learning_map_markdown_rejects_empty_return():
    with pytest.raises(ValueError, match="empty markdown"):
        generate_learning_map_markdown("prompt text", lambda prompt: "  ")


def test_generate_learning_map_markdown_rejects_non_string_return():
    with pytest.raises(TypeError, match="return a string"):
        generate_learning_map_markdown("prompt text", lambda prompt: {"text": "x"})


def test_generate_learning_map_from_artifacts_returns_learning_map():
    sources = [SourceRef(source_id=1, path="README.md", start_line=1, end_line=3)]

    result = generate_learning_map_from_artifacts(
        project_profile={"repository_name": "Demo"},
        sources=sources,
        prompt="prompt text",
        llm_callable=lambda prompt: VALID_MARKDOWN,
    )

    assert isinstance(result, LearningMap)
    assert result.sources == sources
    assert result.project_summary == (
        "This project demonstrates Learning Map generation [Source 1]."
    )
    assert result.starter_questions == [
        "What does the project do?",
        "Where should I start?",
        "Which files matter most?",
    ]


def test_generate_repository_learning_map_runs_on_temp_repo(tmp_path):
    _write_minimal_repo(tmp_path)

    result = generate_repository_learning_map(
        repo_path=tmp_path,
        llm_callable=lambda prompt: VALID_MARKDOWN,
        top_k=4,
    )

    assert result["documents"]
    assert result["chunks"]
    assert result["file_profiles"]
    assert result["project_profile"]
    assert result["sources"]
    assert result["prompt"]
    assert result["markdown"] == VALID_MARKDOWN
    assert isinstance(result["learning_map"], LearningMap)
    assert result["learning_map"].sources == result["sources"]
