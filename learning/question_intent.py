"""Rule-based question intent classification for RepoMind Learning."""

from __future__ import annotations

import re


SUPPORTED_INTENTS = {
    "project_overview",
    "feature_implementation",
    "ai_concept",
    "file_or_symbol",
    "configuration",
    "unsupported",
}

FILE_PATTERN = re.compile(r"\b[\w./-]+\.py\b", re.IGNORECASE)
SYMBOL_PATTERN = re.compile(r"\b[A-Z][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\b")

PROJECT_OVERVIEW_PATTERNS = (
    "what does this project do",
    "what is this project",
    "project overview",
    "repository overview",
    "explain this repo",
    "explain this repository",
    "what does the repo do",
)

CONFIGURATION_TERMS = {
    "api key",
    "config",
    "configuration",
    "configured",
    "dotenv",
    "env",
    "environment",
    "runtime",
    "settings",
}

AI_CONCEPT_TERMS = {
    "agent",
    "attention",
    "embedding",
    "generation",
    "gradient",
    "inference",
    "loss",
    "mask",
    "optimizer",
    "reranker",
    "retrieval",
    "tokenizer",
    "tool calling",
    "training",
}

IMPLEMENTATION_TERMS = {
    "call",
    "called",
    "flow",
    "how",
    "implement",
    "implementation",
    "implemented",
    "pipeline",
    "where",
    "work",
    "works",
}


def classify_question_intent(question: str) -> dict:
    """Classify a repository question with deterministic rules."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string.")

    normalized = _normalize(question)

    if _is_file_or_symbol_question(question, normalized):
        return {
            "intent": "file_or_symbol",
            "confidence": 0.9,
            "reason": "Question names a Python file or qualified symbol.",
        }

    if any(pattern in normalized for pattern in PROJECT_OVERVIEW_PATTERNS):
        return {
            "intent": "project_overview",
            "confidence": 0.88,
            "reason": "Question asks for repository-level purpose or overview.",
        }

    if _contains_any(normalized, CONFIGURATION_TERMS):
        return {
            "intent": "configuration",
            "confidence": 0.86,
            "reason": "Question uses configuration, environment, or runtime terms.",
        }

    if _is_feature_implementation_question(normalized):
        return {
            "intent": "feature_implementation",
            "confidence": 0.84,
            "reason": "Question asks how a feature or flow is implemented.",
        }

    if _contains_any(normalized, AI_CONCEPT_TERMS):
        return {
            "intent": "ai_concept",
            "confidence": 0.78,
            "reason": "Question contains AI or retrieval concept terms.",
        }

    return {
        "intent": "unsupported",
        "confidence": 0.35,
        "reason": "No supported repository-learning intent matched.",
    }


def _normalize(question: str) -> str:
    return " ".join(question.lower().strip().split())


def _is_file_or_symbol_question(raw_question: str, normalized: str) -> bool:
    if FILE_PATTERN.search(raw_question) or SYMBOL_PATTERN.search(raw_question):
        return True
    return " file " in f" {normalized} " and (
        normalized.startswith("explain ")
        or normalized.startswith("what is ")
        or normalized.startswith("where is ")
    )


def _is_feature_implementation_question(normalized: str) -> bool:
    if not _contains_any(normalized, IMPLEMENTATION_TERMS):
        return False
    feature_terms = AI_CONCEPT_TERMS | {
        "answer",
        "chunking",
        "feature",
        "indexing",
        "loop",
        "request",
        "search",
    }
    return _contains_any(normalized, feature_terms)


def _contains_any(text: str, terms: set[str]) -> bool:
    padded = f" {text} "
    return any(f" {term} " in padded or term in text for term in terms)
