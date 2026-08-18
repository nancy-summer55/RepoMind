import pytest

from learning import (
    build_answer_prompt,
    build_answer_sources_context,
    build_concept_answer_prompt,
    build_configuration_answer_prompt,
    build_feature_answer_prompt,
    build_overview_answer_prompt,
    build_refusal_prompt,
)
from learning.schemas import SourceRef


SOURCE = SourceRef(
    source_id=1,
    path="model.py",
    start_line=10,
    end_line=40,
    symbol_name="forward",
    qualified_name="Model.forward",
    source_role="implementation",
)


def _assert_grounded(prompt):
    assert "Repository facts may only come from the provided sources" in prompt
    assert "Every repository fact must cite sources with [Source N]" in prompt
    assert "Do not invent files, classes, functions" in prompt
    assert "If the evidence is insufficient" in prompt
    assert "[Source 1]" in prompt
    assert "File: model.py" in prompt
    assert "Lines: 10-40" in prompt


def test_sources_context_renders_source_ref_and_dict():
    context = build_answer_sources_context(
        [
            SOURCE,
            {
                "document": "def main(): pass",
                "metadata": {
                    "path": "app.py",
                    "start_line": 1,
                    "end_line": 2,
                    "symbol_name": "main",
                },
            },
        ]
    )

    assert "[Source 1]" in context
    assert "Qualified Name: Model.forward" in context
    assert "Source Role: implementation" in context
    assert "[Source 2]" in context
    assert "def main(): pass" in context


def test_feature_prompt_contains_required_sections_and_rules():
    prompt = build_feature_answer_prompt("How does generation work?", [SOURCE])

    for heading in [
        "## Conclusion",
        "## Related Files",
        "## Implementation Flow",
        "## Key Functions",
        "## Source Evidence",
        "## Next Questions",
    ]:
        assert heading in prompt
    _assert_grounded(prompt)


def test_concept_prompt_contains_required_sections_and_rules():
    prompt = build_concept_answer_prompt("What does attention mask do?", [SOURCE])

    for heading in [
        "## Concept",
        "## Where It Appears",
        "## Repository Implementation",
        "## Inputs And Outputs",
        "## Why It Matters",
        "## Source Evidence",
        "## Next Questions",
    ]:
        assert heading in prompt
    _assert_grounded(prompt)


def test_overview_configuration_and_refusal_prompts_have_stable_sections():
    overview = build_overview_answer_prompt("What does this project do?", [SOURCE])
    configuration = build_configuration_answer_prompt(
        "Where is config loaded?",
        [SOURCE],
    )
    refusal = build_refusal_prompt("What is unsupported?", [SOURCE])

    assert "## Summary" in overview
    assert "## Entry Points" in overview
    assert "## Configuration Summary" in configuration
    assert "## Where Values Are Defined" in configuration
    assert "## Unable To Answer" in refusal
    assert "## Missing Evidence" in refusal
    _assert_grounded(overview)
    _assert_grounded(configuration)
    _assert_grounded(refusal)


@pytest.mark.parametrize(
    ("intent", "expected_heading"),
    [
        ("feature_implementation", "## Implementation Flow"),
        ("ai_concept", "## Repository Implementation"),
        ("project_overview", "## Entry Points"),
        ("configuration", "## Runtime Overrides"),
        ("file_or_symbol", "## Definition"),
        ("unsupported", "## Unable To Answer"),
    ],
)
def test_build_answer_prompt_dispatches_by_intent(intent, expected_heading):
    prompt = build_answer_prompt("Question?", intent, [SOURCE])

    assert expected_heading in prompt
    _assert_grounded(prompt)


def test_bad_inputs_raise_clear_errors():
    with pytest.raises(ValueError, match="question must be a non-empty string"):
        build_answer_prompt("", "project_overview", [SOURCE])

    with pytest.raises(ValueError, match="sources must not be empty"):
        build_answer_prompt("Question?", "project_overview", [])

    with pytest.raises(ValueError, match="Unknown intent"):
        build_answer_prompt("Question?", "unknown", [SOURCE])
