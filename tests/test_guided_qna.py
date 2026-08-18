import pytest

from learning import (
    build_guided_answer_artifacts,
    finalize_guided_answer,
    normalize_retrieved_sources,
)
from learning.schemas import AnswerResult, SourceRef


FEATURE_RESULTS = [
    {
        "document": "def generate(): pass",
        "metadata": {
            "path": "sample.py",
            "start_line": 1,
            "end_line": 12,
            "symbol_name": "generate",
            "qualified_name": "GPT.generate",
        },
        "rrf_score": 0.2,
    },
    {
        "document": "class GPT: pass",
        "metadata": {
            "path": "model.py",
            "start_line": 20,
            "end_line": 60,
            "symbol_name": "forward",
            "qualified_name": "GPT.forward",
        },
        "rrf_score": 0.1,
    },
]


def test_normalize_retrieved_sources_preserves_order_and_metadata():
    sources = normalize_retrieved_sources(FEATURE_RESULTS)

    assert [source.source_id for source in sources] == [1, 2]
    assert [source.path for source in sources] == ["sample.py", "model.py"]
    assert sources[0].start_line == 1
    assert sources[0].end_line == 12
    assert sources[0].symbol_name == "generate"
    assert sources[0].qualified_name == "GPT.generate"


def test_feature_question_builds_complete_artifacts():
    artifacts = build_guided_answer_artifacts(
        "How does text generation work?",
        FEATURE_RESULTS,
    )

    assert list(artifacts.keys()) == [
        "intent_result",
        "query_plan",
        "sources",
        "prompt",
        "followups",
    ]
    assert artifacts["intent_result"]["intent"] == "feature_implementation"
    assert artifacts["query_plan"]["queries"]
    assert "## Implementation Flow" in artifacts["prompt"]
    assert len(artifacts["followups"]) == 3
    assert all(source.source_role for source in artifacts["sources"])


def test_concept_question_builds_complete_artifacts():
    artifacts = build_guided_answer_artifacts(
        "What does attention mask do?",
        [
            {
                "metadata": {
                    "path": "model.py",
                    "start_line": 5,
                    "end_line": 18,
                    "symbol_name": "forward",
                }
            }
        ],
    )

    assert artifacts["intent_result"]["intent"] == "ai_concept"
    assert "## Repository Implementation" in artifacts["prompt"]
    assert len(artifacts["followups"]) == 3
    assert artifacts["sources"][0].source_role == "model_logic"


def test_configuration_question_builds_complete_artifacts():
    artifacts = build_guided_answer_artifacts(
        "Where is the config loaded?",
        [
            {
                "metadata": {
                    "path": "config.py",
                    "start_line": 3,
                    "end_line": 9,
                    "symbol_name": "load_config",
                }
            }
        ],
    )

    assert artifacts["intent_result"]["intent"] == "configuration"
    assert "## Runtime Overrides" in artifacts["prompt"]
    assert len(artifacts["followups"]) == 3
    assert artifacts["sources"][0].source_role == "configuration"


def test_finalize_guided_answer_returns_answer_result():
    artifacts = build_guided_answer_artifacts(
        "How does text generation work?",
        FEATURE_RESULTS,
    )

    result = finalize_guided_answer(
        artifacts["intent_result"],
        "Generation is implemented in sample.py [Source 1].",
        artifacts["sources"],
        FEATURE_RESULTS,
        artifacts["followups"],
    )

    assert isinstance(result, AnswerResult)
    assert result.intent == "feature_implementation"
    assert result.answer == "Generation is implemented in sample.py [Source 1]."
    assert result.sources == artifacts["sources"]
    assert result.retrieval_debug == FEATURE_RESULTS
    assert result.followups == artifacts["followups"]
    assert result.refusal is False


def test_finalize_marks_unsupported_intent_as_refusal():
    result = finalize_guided_answer(
        {"intent": "unsupported"},
        "The available evidence is insufficient.",
        [SourceRef(path="README.md", source_role="documentation")],
        [{"metadata": {"path": "README.md"}}],
        ["What source should I inspect next?"],
    )

    assert result.refusal is True
    assert result.intent == "unsupported"


def test_finalize_marks_insufficient_evidence_text_as_refusal():
    result = finalize_guided_answer(
        {"intent": "project_overview"},
        "证据不足，无法可靠回答。",
        [SourceRef(path="README.md", source_role="documentation")],
        [{"metadata": {"path": "README.md"}}],
        [],
    )

    assert result.refusal is True


def test_bad_inputs_raise_clear_errors():
    with pytest.raises(ValueError, match="question must be a non-empty string"):
        build_guided_answer_artifacts("", FEATURE_RESULTS)

    with pytest.raises(ValueError, match="retrieval results must not be empty"):
        build_guided_answer_artifacts("How does generation work?", [])

    with pytest.raises(ValueError, match="answer_text must be a non-empty string"):
        finalize_guided_answer(
            {"intent": "project_overview"},
            "",
            [SourceRef(path="README.md")],
            [{"metadata": {"path": "README.md"}}],
            [],
        )

    with pytest.raises(ValueError, match="retrieval result must include"):
        normalize_retrieved_sources([{"metadata": {}}])
