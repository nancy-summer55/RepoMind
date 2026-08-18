"""Project-level profile aggregation for RepoMind Learning features."""

from __future__ import annotations

from collections import OrderedDict


CATEGORY_RESPONSIBILITY = {
    "entry": "Starts user-facing or executable workflows.",
    "model": "Defines core model or domain behavior.",
    "training": "Runs training or optimization flows.",
    "inference": "Runs inference, generation, or sampling flows.",
    "data": "Loads, prepares, or stores data.",
    "config": "Defines configuration values or settings.",
    "retrieval": "Finds and ranks repository context.",
    "agent": "Coordinates multi-step assistant behavior.",
    "ui": "Renders user interface surfaces.",
    "test": "Verifies behavior.",
    "doc": "Explains usage, architecture, or project context.",
    "utility": "Provides supporting helpers.",
}


def build_project_profile(file_profiles, documents, chunks) -> dict:
    """Aggregate file profiles and source metadata into a stable project dict."""

    ordered_profiles = list(file_profiles)
    entry_files = [
        profile.path
        for profile in ordered_profiles
        if profile.is_entry_candidate
    ]

    return {
        "repository_name": _repository_name(documents),
        "summary_candidates": _summary_candidates(ordered_profiles, documents),
        "entry_files": entry_files,
        "main_modules": _main_modules(ordered_profiles),
        "key_concepts": _key_concepts(ordered_profiles),
        "recommended_reading_order": _recommended_reading_order(ordered_profiles),
        "evidence_sources": _evidence_sources(documents, chunks),
    }


def _repository_name(documents) -> str:
    for document in documents:
        metadata = document.get("metadata", {})
        for key in ("repository_name", "repo_name"):
            value = str(metadata.get(key) or "").strip()
            if value:
                return value
    return ""


def _summary_candidates(file_profiles, documents) -> list[str]:
    candidates = []

    readme = next(
        (
            profile.path
            for profile in file_profiles
            if profile.path.lower().endswith("readme.md")
        ),
        "",
    )
    if readme:
        candidates.append(f"README documentation: {readme}")

    categories = []
    seen_categories = set()
    for profile in file_profiles:
        if profile.category and profile.category not in seen_categories:
            categories.append(profile.category)
            seen_categories.add(profile.category)
    if categories:
        candidates.append("Detected file categories: " + ", ".join(categories))

    if documents:
        candidates.append(f"Indexed documents: {len(documents)}")

    return candidates


def _main_modules(file_profiles) -> list[dict]:
    grouped = OrderedDict()

    for profile in file_profiles:
        category = profile.category or "utility"
        grouped.setdefault(category, []).append(profile)

    modules = []
    for category, profiles in grouped.items():
        ranked_profiles = sorted(
            profiles,
            key=lambda profile: (-profile.importance_score, profile.path),
        )
        modules.append(
            {
                "name": category,
                "responsibility_hint": CATEGORY_RESPONSIBILITY.get(
                    category,
                    CATEGORY_RESPONSIBILITY["utility"],
                ),
                "key_files": [profile.path for profile in ranked_profiles[:5]],
            }
        )

    return modules


def _key_concepts(file_profiles) -> list[str]:
    concepts = []
    seen = set()

    for profile in file_profiles:
        if profile.category and profile.category not in seen:
            concepts.append(profile.category)
            seen.add(profile.category)

        for symbol in profile.symbols:
            tail = symbol.split(".")[-1]
            if tail and tail not in seen:
                concepts.append(tail)
                seen.add(tail)
            if len(concepts) >= 12:
                return concepts

    return concepts


def _recommended_reading_order(file_profiles) -> list[str]:
    docs = [
        profile
        for profile in file_profiles
        if profile.category == "doc"
    ]
    entries = [
        profile
        for profile in file_profiles
        if profile.is_entry_candidate and profile.category != "doc"
    ]
    others = [
        profile
        for profile in file_profiles
        if profile not in docs and profile not in entries
    ]

    ordered = []
    for group in (docs, entries, others):
        for profile in sorted(
            group,
            key=lambda item: (
                _reading_priority(item.path, item.category),
                -item.importance_score,
                item.path,
            ),
        ):
            if profile.path not in ordered:
                ordered.append(profile.path)

    return ordered


def _reading_priority(path: str, category: str) -> int:
    lowered = path.lower()
    filename = lowered.rsplit("/", 1)[-1]

    if filename == "readme.md":
        return 0
    if category == "doc" or lowered.startswith("docs/"):
        return 1
    if filename in {"app.py", "main.py"}:
        return 2
    if filename in {"train.py", "sample.py", "server.py"}:
        return 3
    return 4


def _evidence_sources(documents, chunks) -> list[dict]:
    sources = []
    seen = set()

    for item in chunks:
        metadata = item.get("metadata", {})
        source = _source_from_metadata(metadata)
        key = (
            source.get("path", ""),
            source.get("start_line", 0),
            source.get("end_line", 0),
        )
        if source.get("path") and key not in seen:
            sources.append(source)
            seen.add(key)

    for item in documents:
        metadata = item.get("metadata", {})
        source = _source_from_metadata(metadata)
        key = (
            source.get("path", ""),
            source.get("start_line", 0),
            source.get("end_line", 0),
        )
        if source.get("path") and key not in seen:
            sources.append(source)
            seen.add(key)

    return sources


def _source_from_metadata(metadata: dict) -> dict:
    source = {
        "path": str(metadata.get("path") or ""),
    }
    if metadata.get("start_line") is not None:
        source["start_line"] = int(metadata.get("start_line"))
    if metadata.get("end_line") is not None:
        source["end_line"] = int(metadata.get("end_line"))
    return source
