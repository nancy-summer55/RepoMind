from learning import build_file_profiles


def _doc(path, content="x"):
    suffix = ".md" if path.lower().endswith(".md") else ".py"
    return {
        "content": content,
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


def _profiles_by_path():
    documents = [
        _doc("README.md"),
        _doc("app.py"),
        _doc("main.py"),
        _doc("model.py"),
        _doc("train.py"),
        _doc("sample.py"),
        _doc("utils/helpers.py"),
    ]
    chunks = [
        _chunk("app.py", "ask", "ask"),
        _chunk("main.py", "main", "main"),
        _chunk("model.py", "forward", "Model.forward"),
        _chunk("model.py", "forward", "Model.forward"),
        _chunk("model.py", "generate", "Model.generate"),
        _chunk("train.py", "train", "train"),
        _chunk("sample.py", "generate", "generate"),
        _chunk("utils/helpers.py", "format_name", "format_name"),
    ]
    return {
        profile.path: profile
        for profile in build_file_profiles(documents, chunks)
    }


def test_classifies_required_file_names():
    profiles = _profiles_by_path()

    assert profiles["README.md"].category == "doc"
    assert profiles["app.py"].is_entry_candidate is True
    assert profiles["main.py"].is_entry_candidate is True
    assert profiles["model.py"].category == "model"
    assert profiles["train.py"].category == "training"
    assert profiles["sample.py"].category == "inference"
    assert profiles["train.py"].is_entry_candidate is True
    assert profiles["sample.py"].is_entry_candidate is True


def test_inference_file_names_are_supported():
    profiles = build_file_profiles(
        [_doc("infer.py"), _doc("inference.py")],
        [_chunk("infer.py"), _chunk("inference.py")],
    )

    assert [profile.category for profile in profiles] == [
        "inference",
        "inference",
    ]


def test_symbols_are_deduplicated_with_stable_order():
    profile = build_file_profiles(
        [_doc("model.py")],
        [
            _chunk("model.py", "forward", "Model.forward"),
            _chunk("model.py", "forward", "Model.forward"),
            _chunk("model.py", "generate", "Model.generate"),
        ],
    )[0]

    assert profile.symbols == [
        "Model.forward",
        "forward",
        "Model.generate",
        "generate",
    ]


def test_key_files_score_above_plain_utility():
    profiles = _profiles_by_path()

    assert (
        profiles["model.py"].importance_score
        > profiles["utils/helpers.py"].importance_score
    )
    assert (
        profiles["train.py"].importance_score
        > profiles["utils/helpers.py"].importance_score
    )
    assert profiles["model.py"].evidence
