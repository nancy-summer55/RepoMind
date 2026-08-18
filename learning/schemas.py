"""Serializable dataclass schemas for RepoMind Learning features."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, TypeVar


T = TypeVar("T", bound="_SerializableDataclass")


class _SerializableDataclass:
    """Small shared serializer for plain dataclass models."""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any] | None) -> T:
        if data is None:
            return cls()
        return cls(**data)


@dataclass
class SourceRef(_SerializableDataclass):
    source_id: int = 0
    path: str = ""
    start_line: int = 0
    end_line: int = 0
    symbol_name: str = ""
    qualified_name: str = ""
    source_role: str = ""
    relevance_reason: str = ""


@dataclass
class FileProfile(_SerializableDataclass):
    path: str = ""
    category: str = ""
    symbols: list[str] = field(default_factory=list)
    importance_score: float = 0.0
    is_entry_candidate: bool = False
    evidence: list[str] = field(default_factory=list)


@dataclass
class LearningModule(_SerializableDataclass):
    name: str = ""
    responsibility: str = ""
    key_files: list[str] = field(default_factory=list)
    why_it_matters: str = ""


@dataclass
class ReadingStep(_SerializableDataclass):
    order: int = 0
    title: str = ""
    file_path: str = ""
    reason: str = ""
    expected_takeaway: str = ""


@dataclass
class LearningMap(_SerializableDataclass):
    project_summary: str = ""
    main_modules: list[LearningModule] = field(default_factory=list)
    entry_points: list[SourceRef] = field(default_factory=list)
    core_flow: list[str] = field(default_factory=list)
    reading_order: list[ReadingStep] = field(default_factory=list)
    starter_questions: list[str] = field(default_factory=list)
    sources: list[SourceRef] = field(default_factory=list)
    confidence_notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "LearningMap":
        if data is None:
            return cls()

        payload = dict(data)
        payload["main_modules"] = [
            item
            if isinstance(item, LearningModule)
            else LearningModule.from_dict(item)
            for item in payload.get("main_modules", [])
        ]
        payload["entry_points"] = [
            item if isinstance(item, SourceRef) else SourceRef.from_dict(item)
            for item in payload.get("entry_points", [])
        ]
        payload["reading_order"] = [
            item if isinstance(item, ReadingStep) else ReadingStep.from_dict(item)
            for item in payload.get("reading_order", [])
        ]
        payload["sources"] = [
            item if isinstance(item, SourceRef) else SourceRef.from_dict(item)
            for item in payload.get("sources", [])
        ]

        return cls(**payload)


@dataclass
class AnswerResult(_SerializableDataclass):
    intent: str = ""
    answer: str = ""
    sources: list[SourceRef] = field(default_factory=list)
    followups: list[str] = field(default_factory=list)
    retrieval_debug: list[dict] = field(default_factory=list)
    refusal: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AnswerResult":
        if data is None:
            return cls()

        payload = dict(data)
        payload["sources"] = [
            item if isinstance(item, SourceRef) else SourceRef.from_dict(item)
            for item in payload.get("sources", [])
        ]

        return cls(**payload)
