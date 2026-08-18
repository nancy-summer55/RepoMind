"""Heuristic metadata builders for RepoMind Learning features."""

from __future__ import annotations

from pathlib import PurePosixPath

from learning.schemas import FileProfile


ENTRY_FILES = {
    "app.py",
    "main.py",
    "train.py",
    "sample.py",
    "server.py",
}

IMPORTANT_SYMBOLS = {
    "train",
    "forward",
    "generate",
    "encode",
    "retrieve",
    "ask",
    "main",
}

CATEGORY_PRIORITY = [
    "entry",
    "test",
    "doc",
    "ui",
    "retrieval",
    "agent",
    "training",
    "inference",
    "model",
    "data",
    "config",
    "utility",
]

CATEGORY_LABELS = {
    "entry": "application entry point",
    "model": "model implementation",
    "training": "training flow",
    "inference": "inference or sampling flow",
    "data": "data loading or preparation",
    "config": "configuration",
    "retrieval": "retrieval or RAG behavior",
    "agent": "agent orchestration",
    "ui": "user interface",
    "test": "test coverage",
    "doc": "documentation",
    "utility": "utility code",
}


def build_file_profiles(documents, chunks) -> list[FileProfile]:
    """Build one stable FileProfile per repository-relative file path."""

    paths = _collect_paths(documents, chunks)
    chunks_by_path = _group_chunks_by_path(chunks)
    documents_by_path = _group_documents_by_path(documents)

    profiles = []
    for path in paths:
        file_chunks = chunks_by_path.get(path, [])
        document = documents_by_path.get(path, {})
        symbols = _collect_symbols(file_chunks)
        category, category_evidence = _classify_file(path, symbols)
        importance_score, importance_evidence = _score_file(
            path=path,
            category=category,
            symbols=symbols,
            chunks=file_chunks,
            document=document,
        )
        is_entry_candidate = _is_entry_candidate(path)

        evidence = [
            category_evidence,
            importance_evidence,
        ]
        if is_entry_candidate:
            evidence.append("Marked as entry candidate by filename.")
        if symbols:
            evidence.append(
                "Symbols detected: "
                + ", ".join(symbols[:8])
                + ("." if len(symbols) <= 8 else ", ...")
            )

        profiles.append(
            FileProfile(
                path=path,
                category=category,
                symbols=symbols,
                importance_score=importance_score,
                is_entry_candidate=is_entry_candidate,
                evidence=evidence,
            )
        )

    return profiles


def _collect_paths(documents, chunks) -> list[str]:
    paths = []
    seen = set()

    for item in documents:
        path = _metadata_path(item)
        if path and path not in seen:
            paths.append(path)
            seen.add(path)

    for item in chunks:
        path = _metadata_path(item)
        if path and path not in seen:
            paths.append(path)
            seen.add(path)

    return paths


def _group_documents_by_path(documents) -> dict[str, dict]:
    grouped = {}
    for document in documents:
        path = _metadata_path(document)
        if path and path not in grouped:
            grouped[path] = document
    return grouped


def _group_chunks_by_path(chunks) -> dict[str, list[dict]]:
    grouped = {}
    for chunk in chunks:
        path = _metadata_path(chunk)
        if path:
            grouped.setdefault(path, []).append(chunk)
    return grouped


def _metadata_path(item) -> str:
    metadata = item.get("metadata", {}) if isinstance(item, dict) else {}
    return str(metadata.get("path") or "")


def _collect_symbols(chunks) -> list[str]:
    symbols = []
    seen = set()

    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        candidates = [
            metadata.get("qualified_name"),
            metadata.get("symbol_name"),
        ]
        for candidate in candidates:
            symbol = str(candidate or "").strip()
            if symbol and symbol not in seen:
                symbols.append(symbol)
                seen.add(symbol)

    return symbols


def _classify_file(path: str, symbols: list[str]) -> tuple[str, str]:
    path_obj = PurePosixPath(path)
    filename = path_obj.name.lower()
    directories = {part.lower() for part in path_obj.parts[:-1]}
    symbol_tokens = _symbol_tokens(symbols)

    matches = {
        "entry": filename in {"app.py", "main.py", "server.py"},
        "doc": filename == "readme.md" or "docs" in directories,
        "test": filename.startswith("test_")
        or filename.endswith("_test.py")
        or "test" in directories
        or "tests" in directories,
        "ui": "ui" in directories,
        "retrieval": "retrieval" in directories
        or "retriever" in directories
        or "retriever" in filename
        or "rag" in filename
        or bool(symbol_tokens & {"retrieve"}),
        "agent": "agent" in directories or "agent" in filename,
        "model": filename == "model.py"
        or "model" in directories
        or "models" in directories
        or bool(symbol_tokens & {"forward", "encode", "generate"}),
        "training": filename in {"train.py", "trainer.py"}
        or "train" in directories
        or "training" in directories
        or bool(symbol_tokens & {"train"}),
        "inference": filename in {"sample.py", "infer.py", "inference.py"}
        or "inference" in filename,
        "data": "data" in directories or filename.startswith("data"),
        "config": filename in {"config.py", "settings.py"}
        or "config" in directories
        or "configs" in directories,
    }

    for category in CATEGORY_PRIORITY:
        if category == "utility" or matches.get(category):
            return (
                category,
                f"Classified as {category} from {CATEGORY_LABELS[category]}.",
            )

    return "utility", "Classified as utility from fallback rule."


def _symbol_tokens(symbols: list[str]) -> set[str]:
    tokens = set()
    for symbol in symbols:
        for piece in symbol.replace(".", "_").split("_"):
            token = piece.lower()
            if token in IMPORTANT_SYMBOLS:
                tokens.add(token)
    return tokens


def _score_file(
    path: str,
    category: str,
    symbols: list[str],
    chunks: list[dict],
    document: dict,
) -> tuple[float, str]:
    score = 0.1
    reasons = ["base=0.10"]

    category_weights = {
        "entry": 0.45,
        "model": 0.35,
        "training": 0.35,
        "inference": 0.30,
        "retrieval": 0.30,
        "ui": 0.25,
        "data": 0.20,
        "config": 0.18,
        "agent": 0.18,
        "doc": 0.16,
        "test": 0.12,
        "utility": 0.05,
    }
    category_weight = category_weights.get(category, 0.05)
    score += category_weight
    reasons.append(f"category={category}+{category_weight:.2f}")

    if _is_entry_candidate(path):
        score += 0.20
        reasons.append("entry_filename+0.20")

    important_symbols = _symbol_tokens(symbols)
    if important_symbols:
        symbol_score = min(0.20, 0.05 * len(important_symbols))
        score += symbol_score
        reasons.append(f"important_symbols+{symbol_score:.2f}")

    if len(chunks) > 1:
        chunk_score = min(0.10, 0.02 * len(chunks))
        score += chunk_score
        reasons.append(f"chunk_count+{chunk_score:.2f}")

    content = str(document.get("content") or "")
    if content and len(content) > 2000:
        score += 0.05
        reasons.append("document_size+0.05")

    return round(min(score, 1.0), 3), "Importance score from " + ", ".join(reasons) + "."


def _is_entry_candidate(path: str) -> bool:
    filename = PurePosixPath(path).name.lower()
    return filename in ENTRY_FILES
