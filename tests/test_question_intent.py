import pytest

from learning import classify_question_intent


@pytest.mark.parametrize(
    ("question", "intent"),
    [
        ("How does text generation work?", "feature_implementation"),
        ("What does attention mask do?", "ai_concept"),
        ("Where is the config loaded?", "configuration"),
        ("What does this project do?", "project_overview"),
        ("Explain model.py", "file_or_symbol"),
        ("What is GPT.generate?", "file_or_symbol"),
    ],
)
def test_classifies_required_examples(question, intent):
    result = classify_question_intent(question)

    assert result["intent"] == intent
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["reason"]


def test_empty_question_raises_clear_error():
    with pytest.raises(ValueError, match="question must be a non-empty string"):
        classify_question_intent("  ")


def test_unsupported_question_has_reasonable_confidence():
    result = classify_question_intent("Tell me a joke about pizza.")

    assert result["intent"] == "unsupported"
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["confidence"] < 0.5
