from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RetrievedChunk:
    content: str
    metadata: dict[str, Any]
    score: float | None = None

    @property
    def source_name(self) -> str:
        return str(self.metadata.get("source", "Unknown source"))

    @property
    def page_number(self) -> int | None:
        page_value = self.metadata.get("page")
        if isinstance(page_value, int):
            return page_value
        if isinstance(page_value, str) and page_value.isdigit():
            return int(page_value)
        return None

    @property
    def chunk_id(self) -> int | None:
        chunk_value = self.metadata.get("chunk_id")
        if isinstance(chunk_value, int):
            return chunk_value
        if isinstance(chunk_value, str) and chunk_value.isdigit():
            return int(chunk_value)
        return None

    @property
    def location_label(self) -> str:
        parts = [self.source_name]
        if self.page_number is not None:
            parts.append(f"p.{self.page_number}")
        if self.chunk_id is not None:
            parts.append(f"chunk {self.chunk_id}")
        return " | ".join(parts)

    def excerpt(self, length: int = 320) -> str:
        cleaned = " ".join(self.content.split())
        if len(cleaned) <= length:
            return cleaned
        return f"{cleaned[: length - 3].rstrip()}..."


@dataclass(slots=True)
class AssistantResponse:
    answer: str
    standalone_question: str
    sources: list[RetrievedChunk]


@dataclass(slots=True)
class IngestionSummary:
    document_count: int
    record_count: int
    chunk_count: int
    skipped_files: list[str]
    sources: list[str]
