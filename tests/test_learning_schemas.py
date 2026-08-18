import json

from learning import (
    AnswerResult,
    FileProfile,
    LearningMap,
    LearningModule,
    ReadingStep,
    SourceRef,
)


def test_default_values_are_stable():
    source = SourceRef()
    file_profile = FileProfile()
    learning_map = LearningMap()
    answer = AnswerResult()

    assert source.path == ""
    assert source.start_line == 0
    assert file_profile.symbols == []
    assert file_profile.evidence == []
    assert learning_map.main_modules == []
    assert learning_map.entry_points == []
    assert answer.sources == []
    assert answer.refusal is False


def test_to_dict_returns_json_serializable_structure():
    source = SourceRef(
        source_id=1,
        path="model.py",
        start_line=10,
        end_line=20,
        symbol_name="forward",
        qualified_name="Model.forward",
        source_role="implementation",
        relevance_reason="Defines the core execution path.",
    )

    payload = source.to_dict()

    assert payload == {
        "source_id": 1,
        "path": "model.py",
        "start_line": 10,
        "end_line": 20,
        "symbol_name": "forward",
        "qualified_name": "Model.forward",
        "source_role": "implementation",
        "relevance_reason": "Defines the core execution path.",
    }
    assert json.loads(json.dumps(payload)) == payload


def test_learning_map_nested_round_trip():
    learning_map = LearningMap(
        project_summary="Repository assistant.",
        main_modules=[
            LearningModule(
                name="Retrieval",
                responsibility="Find relevant chunks.",
                key_files=["repo_rag.py"],
                why_it_matters="This is the core answer path.",
            )
        ],
        entry_points=[
            SourceRef(
                source_id=1,
                path="app.py",
                start_line=100,
                end_line=150,
                symbol_name="run_index",
                qualified_name="run_index",
            )
        ],
        core_flow=["load", "chunk", "embed"],
        reading_order=[
            ReadingStep(
                order=1,
                title="Start with the UI entry point",
                file_path="app.py",
                reason="Shows how user actions enter the system.",
                expected_takeaway="Understand Streamlit orchestration.",
            )
        ],
        starter_questions=["How does indexing start?"],
        sources=[
            SourceRef(
                source_id=2,
                path="repo_rag.py",
                start_line=268,
                end_line=520,
            )
        ],
        confidence_notes=["Python and Markdown only."],
    )

    payload = learning_map.to_dict()
    restored = LearningMap.from_dict(payload)

    assert restored == learning_map
    assert isinstance(restored.main_modules[0], LearningModule)
    assert isinstance(restored.entry_points[0], SourceRef)
    assert isinstance(restored.reading_order[0], ReadingStep)
    assert restored.main_modules[0].key_files == ["repo_rag.py"]
    assert restored.entry_points[0].qualified_name == "run_index"
    assert restored.reading_order[0].order == 1


def test_answer_result_nested_round_trip():
    answer = AnswerResult(
        intent="overview",
        answer="Indexing starts in app.py.",
        sources=[
            SourceRef(
                source_id=1,
                path="app.py",
                start_line=90,
                end_line=150,
                source_role="entry_point",
            )
        ],
        followups=["Where are chunks created?"],
        retrieval_debug=[
            {
                "vector_rank": 1,
                "bm25_rank": 2,
                "rrf_score": 0.031,
                "metadata": {"path": "app.py"},
            }
        ],
        refusal=False,
    )

    payload = answer.to_dict()
    restored = AnswerResult.from_dict(payload)

    assert restored == answer
    assert isinstance(restored.sources[0], SourceRef)
    assert restored.followups == ["Where are chunks created?"]
    assert restored.retrieval_debug[0]["metadata"]["path"] == "app.py"
