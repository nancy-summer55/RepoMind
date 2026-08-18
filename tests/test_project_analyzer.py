from learning import build_file_profiles, build_project_profile


def _doc(path, content="x", repo_name=""):
    suffix = ".md" if path.lower().endswith(".md") else ".py"
    metadata = {
        "path": path,
        "extension": suffix,
        "language": "markdown" if suffix == ".md" else "python",
    }
    if repo_name:
        metadata["repository_name"] = repo_name
    return {
        "content": content,
        "metadata": metadata,
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


def _profile():
    documents = [
        _doc("README.md", repo_name="RepoMind"),
        _doc("docs/guide.md"),
        _doc("app.py"),
        _doc("model.py"),
        _doc("train.py"),
        _doc("retrieval/search.py"),
    ]
    chunks = [
        _chunk("README.md", start_line=1, end_line=20),
        _chunk("app.py", "ask", "ask", start_line=30, end_line=80),
        _chunk("model.py", "forward", "Model.forward", start_line=10, end_line=40),
        _chunk("train.py", "train", "train", start_line=1, end_line=50),
        _chunk(
            "retrieval/search.py",
            "retrieve",
            "retrieve",
            start_line=5,
            end_line=25,
        ),
    ]
    file_profiles = build_file_profiles(documents, chunks)
    return build_project_profile(file_profiles, documents, chunks)


def test_builds_stable_project_profile_shape():
    profile = _profile()

    assert profile["repository_name"] == "RepoMind"
    assert list(profile.keys()) == [
        "repository_name",
        "summary_candidates",
        "entry_files",
        "main_modules",
        "key_concepts",
        "recommended_reading_order",
        "evidence_sources",
    ]
    assert profile == _profile()


def test_entry_files_keep_file_profile_order():
    profile = _profile()

    assert profile["entry_files"] == ["app.py", "train.py"]


def test_recommended_reading_order_prefers_readme():
    profile = _profile()

    assert profile["recommended_reading_order"][0] == "README.md"
    assert profile["recommended_reading_order"][1] == "docs/guide.md"
    assert "app.py" in profile["recommended_reading_order"][2:]


def test_main_modules_include_existing_categories():
    profile = _profile()
    module_names = {
        module["name"]
        for module in profile["main_modules"]
    }

    assert {"doc", "entry", "model", "retrieval"} <= module_names
    for module in profile["main_modules"]:
        assert module["responsibility_hint"]
        assert module["key_files"]


def test_evidence_sources_are_non_empty_and_stable():
    profile = _profile()

    assert profile["evidence_sources"]
    assert profile["evidence_sources"][0] == {
        "path": "README.md",
        "start_line": 1,
        "end_line": 20,
    }
    assert profile["evidence_sources"] == _profile()["evidence_sources"]
