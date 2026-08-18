"""Rule-based follow-up question generation."""

from __future__ import annotations

from learning.answer_composer import SUPPORTED_INTENTS
from learning.schemas import SourceRef


def generate_followups(question, intent, sources, limit=3) -> list[str]:
    """Generate stable follow-up questions without calling an LLM."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string.")
    if intent not in SUPPORTED_INTENTS:
        raise ValueError(f"Unknown intent: {intent}")
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer.")

    source_refs = [_source_ref(source) for source in sources or []]
    primary_path = _primary_path(source_refs)
    primary_symbol = _primary_symbol(source_refs)

    candidates = []
    if intent == "feature_implementation":
        candidates.extend(
            [
                f"What implementation details in {primary_path} should I inspect next?",
                f"Which functions call or depend on {primary_symbol}?",
                "What inputs and outputs drive this implementation flow?",
            ]
        )
    elif intent == "ai_concept":
        candidates.extend(
            [
                f"Where does this concept appear in the code around {primary_path}?",
                f"Which implementation is most related to {primary_symbol}?",
                "What inputs and outputs make this concept visible?",
            ]
        )
    elif intent == "project_overview":
        candidates.extend(
            [
                f"Which file should I read first after {primary_path}?",
                "What is the main runtime flow through this repository?",
                "Which modules are most important for a first pass?",
            ]
        )
    elif intent == "configuration":
        candidates.extend(
            [
                f"Where is configuration read or overridden near {primary_path}?",
                "Which environment variables or defaults affect runtime behavior?",
                "What happens if these configuration values are missing?",
            ]
        )
    elif intent == "file_or_symbol":
        candidates.extend(
            [
                f"What responsibilities does {primary_symbol} have?",
                f"Where is {primary_symbol} used from {primary_path}?",
                "What should I read next to understand this symbol in context?",
            ]
        )
    else:
        candidates.extend(
            [
                f"What available evidence exists in {primary_path}?",
                "What narrower repository question can be answered from these sources?",
                "Which source should I inspect next?",
            ]
        )

    return _dedupe_non_empty(candidates)[:limit]


def _source_ref(source) -> SourceRef:
    if isinstance(source, SourceRef):
        return source
    if not isinstance(source, dict):
        return SourceRef()

    metadata = source.get("metadata", source)
    return SourceRef(
        path=str(metadata.get("path") or ""),
        start_line=int(metadata.get("start_line") or 0),
        end_line=int(metadata.get("end_line") or 0),
        symbol_name=str(metadata.get("symbol_name") or ""),
        qualified_name=str(metadata.get("qualified_name") or ""),
    )


def _primary_path(sources: list[SourceRef]) -> str:
    for source in sources:
        if source.path:
            return source.path
    return "the selected sources"


def _primary_symbol(sources: list[SourceRef]) -> str:
    for source in sources:
        symbol = source.qualified_name or source.symbol_name
        if symbol:
            return symbol
    return "the selected symbol"


def _dedupe_non_empty(values: list[str]) -> list[str]:
    output = []
    seen = set()
    for value in values:
        cleaned = " ".join(value.strip().split())
        if cleaned and cleaned not in seen:
            output.append(cleaned)
            seen.add(cleaned)
    return output
