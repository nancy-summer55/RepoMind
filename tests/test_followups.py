import pytest

from learning import generate_followups
from learning.schemas import SourceRef


SOURCE = SourceRef(
    path="model.py",
    start_line=10,
    end_line=40,
    symbol_name="forward",
    qualified_name="Model.forward",
)


@pytest.mark.parametrize(
    "intent",
    [
        "project_overview",
        "feature_implementation",
        "ai_concept",
        "file_or_symbol",
        "configuration",
        "unsupported",
    ],
)
def test_each_intent_returns_three_stable_unique_followups(intent):
    first = generate_followups("Question?", intent, [SOURCE])
    second = generate_followups("Question?", intent, [SOURCE])

    assert first == second
    assert len(first) == 3
    assert len(set(first)) == 3
    assert all(question.strip() for question in first)


def test_feature_followup_mentions_implementation_detail():
    followups = generate_followups(
        "How does generation work?",
        "feature_implementation",
        [SOURCE],
    )

    assert any("implementation details" in item for item in followups)
    assert any("Model.forward" in item for item in followups)


def test_concept_followup_mentions_code_location_or_related_implementation():
    followups = generate_followups(
        "What does attention mask do?",
        "ai_concept",
        [SOURCE],
    )

    assert any("Where does this concept appear" in item for item in followups)
    assert any("Model.forward" in item for item in followups)


def test_overview_followup_mentions_which_file_to_read():
    followups = generate_followups(
        "What does this project do?",
        "project_overview",
        [SOURCE],
    )

    assert any("Which file should I read first" in item for item in followups)


def test_configuration_followup_mentions_read_or_override():
    followups = generate_followups(
        "Where is config loaded?",
        "configuration",
        [SOURCE],
    )

    assert any("read or overridden" in item for item in followups)


def test_dict_sources_are_supported():
    followups = generate_followups(
        "Explain model.py",
        "file_or_symbol",
        [
            {
                "metadata": {
                    "path": "model.py",
                    "symbol_name": "forward",
                    "qualified_name": "Model.forward",
                }
            }
        ],
    )

    assert any("Model.forward" in item for item in followups)
    assert any("model.py" in item for item in followups)


def test_bad_inputs_raise_clear_errors():
    with pytest.raises(ValueError, match="question must be a non-empty string"):
        generate_followups("", "project_overview", [SOURCE])

    with pytest.raises(ValueError, match="Unknown intent"):
        generate_followups("Question?", "unknown", [SOURCE])
