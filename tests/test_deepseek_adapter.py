import pytest

from learning import (
    build_deepseek_llm_callable,
    generate_repository_learning_map_with_client,
)
from learning.schemas import LearningMap


VALID_MARKDOWN = """
## What This Project Does
This project can be summarized from selected sources [Source 1].

## Starter Questions
- What does this project do?
- Where should I start?
- Which file should I read next?

## Confidence Notes
- The fake response is test-only.
"""


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, content, calls):
        self.content = content
        self.calls = calls

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(self.content)


class FakeChat:
    def __init__(self, content, calls):
        self.completions = FakeCompletions(content, calls)


class FakeClient:
    def __init__(self, content, calls):
        self.chat = FakeChat(content, calls)


def _factory(content=VALID_MARKDOWN):
    calls = []

    def client_factory():
        return FakeClient(content, calls)

    return client_factory, calls


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


def test_fake_client_returns_valid_markdown_and_receives_prompt():
    client_factory, calls = _factory()
    llm = build_deepseek_llm_callable(client_factory, "deepseek-chat")

    markdown = llm("prompt text")

    assert markdown == VALID_MARKDOWN
    assert calls[0]["model"] == "deepseek-chat"
    assert calls[0]["messages"] == [
        {
            "role": "user",
            "content": "prompt text",
        }
    ]
    assert calls[0]["stream"] is False


def test_rejects_non_callable_factory():
    with pytest.raises(TypeError, match="client_factory must be callable"):
        build_deepseek_llm_callable(None, "deepseek-chat")


def test_rejects_empty_model_name():
    with pytest.raises(ValueError, match="model_name must be a non-empty string"):
        build_deepseek_llm_callable(lambda: object(), "")


def test_rejects_non_string_response_content():
    client_factory, _ = _factory(content={"markdown": "x"})
    llm = build_deepseek_llm_callable(client_factory, "deepseek-chat")

    with pytest.raises(TypeError, match="response content must be a string"):
        llm("prompt text")


def test_rejects_empty_response_content():
    client_factory, _ = _factory(content="  ")
    llm = build_deepseek_llm_callable(client_factory, "deepseek-chat")

    with pytest.raises(ValueError, match="response content was empty"):
        llm("prompt text")


def test_generate_repository_learning_map_with_client_runs_on_temp_repo(tmp_path):
    _write_minimal_repo(tmp_path)
    client_factory, calls = _factory()

    result = generate_repository_learning_map_with_client(
        repo_path=tmp_path,
        client_factory=client_factory,
        model_name="deepseek-chat",
        top_k=3,
    )

    assert result["prompt"]
    assert result["sources"]
    assert result["markdown"] == VALID_MARKDOWN
    assert isinstance(result["learning_map"], LearningMap)
    assert calls
    assert calls[0]["messages"][0]["content"] == result["prompt"]
