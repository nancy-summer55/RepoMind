import pytest

from learning import label_source, label_sources
from learning.schemas import SourceRef


@pytest.mark.parametrize(
    ("source", "expected_role"),
    [
        ({"metadata": {"path": "README.md"}}, "documentation"),
        ({"metadata": {"path": "docs/guide.md"}}, "documentation"),
        ({"metadata": {"path": "app.py"}}, "entry_point"),
        ({"metadata": {"path": "main.py"}}, "entry_point"),
        ({"metadata": {"path": "model.py"}}, "model_logic"),
        ({"metadata": {"path": "layers.py", "symbol_name": "forward"}}, "model_logic"),
        ({"metadata": {"path": "train.py"}}, "training_logic"),
        ({"metadata": {"path": "trainer.py", "symbol_name": "train"}}, "training_logic"),
        ({"metadata": {"path": "sample.py"}}, "inference_logic"),
        ({"metadata": {"path": "inference.py", "symbol_name": "generate"}}, "inference_logic"),
        ({"metadata": {"path": "config.py"}}, "configuration"),
        ({"metadata": {"path": "settings.py"}}, "configuration"),
        ({"metadata": {"path": "tests/test_model.py"}}, "test"),
    ],
)
def test_label_source_classifies_common_paths_and_symbols(source, expected_role):
    labeled = label_source(source)

    assert labeled.source_role == expected_role
    assert labeled.relevance_reason


def test_label_source_preserves_existing_source_ref_location_fields():
    source = SourceRef(
        source_id=7,
        path="model.py",
        start_line=10,
        end_line=42,
        symbol_name="forward",
        qualified_name="GPT.forward",
    )

    labeled = label_source(source)

    assert labeled.source_id == 7
    assert labeled.path == "model.py"
    assert labeled.start_line == 10
    assert labeled.end_line == 42
    assert labeled.symbol_name == "forward"
    assert labeled.qualified_name == "GPT.forward"
    assert labeled.source_role == "model_logic"
    assert labeled.relevance_reason


def test_label_source_supports_fallback_path():
    labeled = label_source(
        {"metadata": {"start_line": 1, "end_line": 5}},
        fallback_path="config/settings.py",
    )

    assert labeled.path == "config/settings.py"
    assert labeled.source_role == "configuration"


def test_sample_generate_can_be_inference_or_core_implementation():
    labeled = label_source(
        {
            "metadata": {
                "path": "sample.py",
                "symbol_name": "generate",
                "qualified_name": "GPT.generate",
            }
        }
    )

    assert labeled.source_role in {"inference_logic", "core_implementation"}
    assert labeled.relevance_reason


def test_label_sources_keeps_stable_input_order():
    sources = [
        {"metadata": {"path": "README.md"}},
        {"metadata": {"path": "app.py"}},
        {"metadata": {"path": "model.py", "symbol_name": "forward"}},
    ]

    labeled = label_sources(sources)

    assert [source.path for source in labeled] == ["README.md", "app.py", "model.py"]
    assert [source.source_role for source in labeled] == [
        "documentation",
        "entry_point",
        "model_logic",
    ]
    assert all(source.relevance_reason for source in labeled)


def test_label_source_rejects_empty_or_unparseable_source():
    with pytest.raises(ValueError, match="source must not be empty"):
        label_source({})

    with pytest.raises(ValueError, match="source must include"):
        label_source({"metadata": {}})

    with pytest.raises(TypeError, match="source must be a dict or SourceRef"):
        label_source(object())


def test_label_sources_rejects_empty_input():
    with pytest.raises(ValueError, match="sources must not be empty"):
        label_sources([])
