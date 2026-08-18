"""Pure orchestration helpers for Guided Q&A artifacts."""

from __future__ import annotations

from learning.answer_composer import build_answer_prompt
from learning.followups import generate_followups
from learning.query_planner import plan_queries
from learning.question_intent import classify_question_intent
from learning.schemas import AnswerResult, SourceRef
from learning.source_labeler import label_sources


INSUFFICIENT_EVIDENCE_MARKERS = (
    "insufficient evidence",
    "not enough evidence",
    "evidence is insufficient",
    "available evidence is insufficient",
    "无法回答",
    "证据不足",
    "信息不足",
)


def normalize_retrieved_sources(results) -> list[SourceRef]:
    """Convert repo_rag-style retrieval results into SourceRef objects."""

    if not results:
        raise ValueError("retrieval results must not be empty.")
    if not isinstance(results, list):
        raise TypeError("retrieval results must be a list.")

    sources = []
    for index, result in enumerate(results, start=1):
        if isinstance(result, SourceRef):
            if not result.path and not result.symbol_name and not result.qualified_name:
                raise ValueError("retrieval result must include source metadata.")
            sources.append(
                SourceRef(
                    source_id=result.source_id or index,
                    path=result.path,
                    start_line=result.start_line,
                    end_line=result.end_line,
                    symbol_name=result.symbol_name,
                    qualified_name=result.qualified_name,
                    source_role=result.source_role,
                    relevance_reason=result.relevance_reason,
                )
            )
            continue

        if not isinstance(result, dict):
            raise TypeError("retrieval results must contain dict or SourceRef items.")

        metadata = result.get("metadata", result)
        if not isinstance(metadata, dict):
            raise ValueError("retrieval result metadata must be a dict.")

        path = str(metadata.get("path") or result.get("path") or "")
        symbol_name = str(metadata.get("symbol_name") or result.get("symbol_name") or "")
        qualified_name = str(
            metadata.get("qualified_name") or result.get("qualified_name") or ""
        )
        if not path and not symbol_name and not qualified_name:
            raise ValueError("retrieval result must include source metadata.")

        sources.append(
            SourceRef(
                source_id=_to_int(result.get("source_id") or metadata.get("source_id"))
                or index,
                path=path,
                start_line=_to_int(
                    metadata.get("start_line") or result.get("start_line")
                ),
                end_line=_to_int(metadata.get("end_line") or result.get("end_line")),
                symbol_name=symbol_name,
                qualified_name=qualified_name,
                source_role=str(
                    metadata.get("source_role") or result.get("source_role") or ""
                ),
                relevance_reason=str(
                    metadata.get("relevance_reason")
                    or result.get("relevance_reason")
                    or ""
                ),
            )
        )

    return sources


def build_guided_answer_artifacts(
    question,
    retrieval_results,
    user_language="Chinese",
) -> dict:
    """Build deterministic Guided Q&A artifacts without calling an LLM."""

    intent_result = classify_question_intent(question)
    intent = intent_result["intent"]
    query_plan = plan_queries(question, intent)
    sources = label_sources(normalize_retrieved_sources(retrieval_results))
    prompt = build_answer_prompt(question, intent, sources, user_language)
    followups = generate_followups(question, intent, sources, limit=3)

    return {
        "intent_result": intent_result,
        "query_plan": query_plan,
        "sources": sources,
        "prompt": prompt,
        "followups": followups,
    }


def finalize_guided_answer(
    intent_result,
    answer_text,
    sources,
    retrieval_results,
    followups,
) -> AnswerResult:
    """Wrap a generated guided answer in the shared AnswerResult schema."""

    if not isinstance(intent_result, dict):
        raise TypeError("intent_result must be a dict.")
    intent = str(intent_result.get("intent") or "")
    if not intent:
        raise ValueError("intent_result must include an intent.")
    if not isinstance(answer_text, str) or not answer_text.strip():
        raise ValueError("answer_text must be a non-empty string.")

    source_refs = _ensure_source_refs(sources)
    refusal = intent == "unsupported" or _mentions_insufficient_evidence(answer_text)

    return AnswerResult(
        intent=intent,
        answer=answer_text.strip(),
        sources=source_refs,
        followups=list(followups or []),
        retrieval_debug=list(retrieval_results or []),
        refusal=refusal,
    )


def _ensure_source_refs(sources) -> list[SourceRef]:
    if not sources:
        return []

    output = []
    for source in sources:
        if isinstance(source, SourceRef):
            output.append(source)
        elif isinstance(source, dict):
            output.extend(normalize_retrieved_sources([source]))
        else:
            raise TypeError("sources must contain dict or SourceRef items.")
    return output


def _mentions_insufficient_evidence(answer_text: str) -> bool:
    lowered = answer_text.lower()
    return any(marker in lowered for marker in INSUFFICIENT_EVIDENCE_MARKERS)


def _to_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
