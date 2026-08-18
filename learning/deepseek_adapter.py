"""DeepSeek-compatible adapter for injectable Learning Map generation."""

from __future__ import annotations

from learning.learning_generator import generate_repository_learning_map


def build_deepseek_llm_callable(client_factory, model_name):
    """Return an llm_callable(prompt) compatible with learning_generator."""

    if not callable(client_factory):
        raise TypeError("client_factory must be callable.")
    if not isinstance(model_name, str) or not model_name.strip():
        raise ValueError("model_name must be a non-empty string.")

    def llm_callable(prompt) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string.")

        client = client_factory()
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            stream=False,
        )
        content = response.choices[0].message.content
        if not isinstance(content, str):
            raise TypeError("DeepSeek response content must be a string.")
        if not content.strip():
            raise ValueError("DeepSeek response content was empty.")

        return content

    return llm_callable


def generate_repository_learning_map_with_client(
    repo_path,
    client_factory,
    model_name,
    chunk_size=1200,
    chunk_overlap=200,
    chunk_strategy="ast",
    user_language="Chinese",
    top_k=8,
) -> dict:
    """Generate a repository Learning Map using an injected client factory."""

    llm_callable = build_deepseek_llm_callable(
        client_factory=client_factory,
        model_name=model_name,
    )
    return generate_repository_learning_map(
        repo_path=repo_path,
        llm_callable=llm_callable,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunk_strategy=chunk_strategy,
        user_language=user_language,
        top_k=top_k,
    )
