import pytest

from learning import plan_queries


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
def test_each_intent_generates_stable_query_structure(intent):
    first = plan_queries("How does attention mask work?", intent)
    second = plan_queries("How does attention mask work?", intent)

    assert first == second
    assert list(first.keys()) == ["intent", "queries", "hints"]
    assert first["intent"] == intent
    assert first["queries"]
    assert first["hints"]


def test_concept_question_expands_related_terms():
    result = plan_queries("What does attention mask do?", "ai_concept")

    joined = " ".join(result["queries"])
    assert "attention" in joined
    assert "attention mask" in joined
    assert "causal mask" in joined


@pytest.mark.parametrize(
    ("question", "expected_terms"),
    [
        ("embedding", ["token embedding", "position embedding"]),
        ("tokenizer", ["tokenization", "tokens"]),
        ("loss", ["cross entropy", "objective"]),
        ("optimizer", ["adam", "learning rate"]),
        ("training", ["train loop", "optimizer step"]),
        ("inference", ["sampling", "generation"]),
        ("generation", ["generate", "sampling"]),
        ("retrieval", ["search", "ranking"]),
        ("reranker", ["rerank", "cross encoder"]),
        ("agent", ["planner", "orchestration"]),
        ("tool calling", ["tools", "function calling"]),
    ],
)
def test_concept_expansions_cover_required_terms(question, expected_terms):
    result = plan_queries(question, "ai_concept")
    joined = " ".join(result["queries"])

    for term in expected_terms:
        assert term in joined


def test_feature_implementation_adds_implementation_terms():
    result = plan_queries("How does text generation work?", "feature_implementation")
    joined = " ".join(result["queries"])

    assert "implementation call flow" in joined
    assert "function class method pipeline" in joined


def test_configuration_adds_config_runtime_terms():
    result = plan_queries("Where is the config loaded?", "configuration")
    joined = " ".join(result["queries"])

    assert "config settings environment" in joined
    assert "env runtime api key defaults" in joined


def test_project_overview_adds_readme_architecture_terms():
    result = plan_queries("What does this project do?", "project_overview")
    joined = " ".join(result["queries"])

    assert "README project overview architecture main entry files" in joined


def test_empty_question_or_unknown_intent_raises_clear_error():
    with pytest.raises(ValueError, match="question must be a non-empty string"):
        plan_queries("", "project_overview")

    with pytest.raises(ValueError, match="Unknown intent"):
        plan_queries("What does this project do?", "unknown")
