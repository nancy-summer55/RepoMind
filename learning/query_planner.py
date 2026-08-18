"""Deterministic query planning for RepoMind Learning."""

from __future__ import annotations


SUPPORTED_INTENTS = {
    "project_overview",
    "feature_implementation",
    "ai_concept",
    "file_or_symbol",
    "configuration",
    "unsupported",
}

CONCEPT_EXPANSIONS = {
    "attention": ["attention", "self attention", "attention mask"],
    "mask": ["mask", "attention mask", "causal mask"],
    "embedding": ["embedding", "token embedding", "position embedding"],
    "tokenizer": ["tokenizer", "tokenization", "tokens"],
    "loss": ["loss", "cross entropy", "objective"],
    "optimizer": ["optimizer", "adam", "learning rate"],
    "training": ["training", "train loop", "optimizer step"],
    "inference": ["inference", "sampling", "generation"],
    "generation": ["generation", "generate", "sampling"],
    "retrieval": ["retrieval", "search", "ranking"],
    "reranker": ["reranker", "rerank", "cross encoder"],
    "agent": ["agent", "planner", "orchestration"],
    "tool calling": ["tool calling", "tools", "function calling"],
}


def plan_queries(question: str, intent: str) -> dict:
    """Return stable retrieval query candidates for a classified intent."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string.")
    if intent not in SUPPORTED_INTENTS:
        raise ValueError(f"Unknown intent: {intent}")

    cleaned = " ".join(question.strip().split())
    queries = [cleaned]
    hints = []

    if intent == "project_overview":
        queries.extend(
            [
                "README project overview architecture main entry files",
                "main app entry point repository structure",
            ]
        )
        hints.append("Prefer README, docs, entry files, and architecture notes.")
    elif intent == "feature_implementation":
        queries.extend(
            [
                f"{cleaned} implementation call flow",
                f"{cleaned} function class method pipeline",
            ]
        )
        hints.append("Prefer implementation chunks and direct call flow evidence.")
    elif intent == "ai_concept":
        queries.extend(_concept_expansions(cleaned))
        queries.append(f"{cleaned} implementation explanation")
        hints.append("Expand AI/retrieval concept vocabulary before retrieval.")
    elif intent == "file_or_symbol":
        queries.extend(
            [
                f"{cleaned} definition",
                f"{cleaned} references symbol file",
            ]
        )
        hints.append("Prefer exact file path, symbol name, and qualified name matches.")
    elif intent == "configuration":
        queries.extend(
            [
                f"{cleaned} config settings environment",
                "config settings env runtime api key defaults",
            ]
        )
        hints.append("Prefer config files, environment variables, and runtime defaults.")
    else:
        queries.append(f"{cleaned} repository context")
        hints.append("Intent is unsupported; keep retrieval narrow and grounded.")

    return {
        "intent": intent,
        "queries": _dedupe(queries),
        "hints": hints,
    }


def _concept_expansions(question: str) -> list[str]:
    lowered = question.lower()
    expansions = []
    for term, values in CONCEPT_EXPANSIONS.items():
        if term in lowered:
            expansions.extend(values)
    if not expansions:
        expansions.append("AI concept implementation explanation")
    return expansions


def _dedupe(values: list[str]) -> list[str]:
    output = []
    seen = set()
    for value in values:
        cleaned = " ".join(str(value).strip().split())
        if cleaned and cleaned not in seen:
            output.append(cleaned)
            seen.add(cleaned)
    return output
