"""Rule-based source role labeling for guided answers."""

from __future__ import annotations

from pathlib import PurePosixPath

from learning.schemas import SourceRef


SOURCE_ROLES = {
    "entry_point",
    "core_implementation",
    "model_logic",
    "training_logic",
    "inference_logic",
    "data_processing",
    "configuration",
    "documentation",
    "utility",
    "test",
}


def label_source(source: dict | SourceRef, fallback_path: str = "") -> SourceRef:
    """Return a SourceRef with a stable role and reason."""

    ref = _to_source_ref(source, fallback_path)
    if not ref.path and not ref.symbol_name and not ref.qualified_name:
        raise ValueError("source must include a path, symbol_name, or qualified_name.")

    role, reason = _classify_source(ref)
    return SourceRef(
        source_id=ref.source_id,
        path=ref.path,
        start_line=ref.start_line,
        end_line=ref.end_line,
        symbol_name=ref.symbol_name,
        qualified_name=ref.qualified_name,
        source_role=role,
        relevance_reason=reason,
    )


def label_sources(sources: list[dict] | list[SourceRef]) -> list[SourceRef]:
    """Label sources in input order."""

    if not sources:
        raise ValueError("sources must not be empty.")
    return [label_source(source) for source in sources]


def _to_source_ref(source: dict | SourceRef, fallback_path: str) -> SourceRef:
    if isinstance(source, SourceRef):
        path = source.path or fallback_path
        return SourceRef(
            source_id=source.source_id,
            path=path,
            start_line=source.start_line,
            end_line=source.end_line,
            symbol_name=source.symbol_name,
            qualified_name=source.qualified_name,
            source_role=source.source_role,
            relevance_reason=source.relevance_reason,
        )

    if not isinstance(source, dict):
        raise TypeError("source must be a dict or SourceRef.")
    if not source:
        raise ValueError("source must not be empty.")

    metadata = source.get("metadata", source)
    if not isinstance(metadata, dict):
        raise ValueError("source metadata must be a dict.")

    path = str(metadata.get("path") or source.get("path") or fallback_path or "")
    return SourceRef(
        source_id=_to_int(source.get("source_id") or metadata.get("source_id")),
        path=path,
        start_line=_to_int(metadata.get("start_line") or source.get("start_line")),
        end_line=_to_int(metadata.get("end_line") or source.get("end_line")),
        symbol_name=str(
            metadata.get("symbol_name") or source.get("symbol_name") or ""
        ),
        qualified_name=str(
            metadata.get("qualified_name") or source.get("qualified_name") or ""
        ),
        source_role=str(metadata.get("source_role") or source.get("source_role") or ""),
        relevance_reason=str(
            metadata.get("relevance_reason") or source.get("relevance_reason") or ""
        ),
    )


def _classify_source(ref: SourceRef) -> tuple[str, str]:
    path_obj = PurePosixPath(ref.path.replace("\\", "/"))
    filename = path_obj.name.lower()
    directories = {part.lower() for part in path_obj.parts[:-1]}
    symbol_text = f"{ref.qualified_name} {ref.symbol_name}".lower()

    if filename == "readme.md" or "docs" in directories or filename.endswith(".md"):
        return "documentation", _reason("documentation", "README, docs path, or Markdown file", ref)

    if _in_path(directories, {"test", "tests"}) or filename.startswith("test_") or filename.endswith("_test.py"):
        return "test", _reason("test", "test directory or test filename", ref)

    if filename in {"app.py", "main.py", "server.py"} or _has_symbol(symbol_text, {"main", "ask", "run_index"}):
        return "entry_point", _reason("entry_point", "entry filename or entry-like symbol", ref)

    if filename in {"config.py", "settings.py"} or _in_path(directories, {"config", "configs"}) or _has_symbol(
        symbol_text,
        {"config", "settings", "env", "environment"},
    ):
        return "configuration", _reason("configuration", "config filename, directory, or symbol keyword", ref)

    if filename in {"train.py", "trainer.py"} or _in_path(directories, {"train", "training"}) or _has_symbol(
        symbol_text,
        {"train", "trainer", "fit", "loss", "optimizer"},
    ):
        return "training_logic", _reason("training_logic", "training filename, directory, or symbol keyword", ref)

    if filename in {"sample.py", "infer.py", "inference.py"} or "inference" in filename or _has_symbol(
        symbol_text,
        {"generate", "infer", "inference", "sample", "predict"},
    ):
        return "inference_logic", _reason("inference_logic", "inference filename or symbol keyword", ref)

    if filename == "model.py" or _in_path(directories, {"model", "models"}) or _has_symbol(
        symbol_text,
        {"model", "forward", "encode", "decode", "attention", "embedding"},
    ):
        return "model_logic", _reason("model_logic", "model filename, directory, or symbol keyword", ref)

    if _in_path(directories, {"data", "dataset", "datasets"}) or filename.startswith("data") or _has_symbol(
        symbol_text,
        {"load_data", "dataset", "dataloader", "tokenizer"},
    ):
        return "data_processing", _reason("data_processing", "data path or data-processing symbol keyword", ref)

    if _in_path(directories, {"retrieval", "retriever", "rag", "agent", "agents", "learning"}) or _has_symbol(
        symbol_text,
        {"retrieve", "rerank", "search", "rag", "agent", "plan"},
    ):
        return "core_implementation", _reason("core_implementation", "retrieval, agent, or core workflow keyword", ref)

    return "utility", _reason("utility", "fallback rule for supporting code", ref)


def _reason(role: str, rule: str, ref: SourceRef) -> str:
    target = ref.path or ref.qualified_name or ref.symbol_name
    return f"Labeled as {role} because {target} matched {rule}."


def _has_symbol(symbol_text: str, keywords: set[str]) -> bool:
    normalized = symbol_text.replace(".", "_").replace("-", "_")
    parts = {part for part in normalized.split("_") if part}
    return bool(parts & keywords) or any(keyword in normalized for keyword in keywords)


def _in_path(directories: set[str], names: set[str]) -> bool:
    return bool(directories & names)


def _to_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
