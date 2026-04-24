from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Iterable, Protocol

from langchain_core.documents import Document
from PyPDF2 import PdfReader


class UploadLike(Protocol):
    name: str

    def getvalue(self) -> bytes:
        ...


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def load_documents(files: Iterable[UploadLike]) -> tuple[list[Document], list[str]]:
    documents: list[Document] = []
    skipped_files: list[str] = []

    for uploaded_file in files:
        suffix = Path(uploaded_file.name).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            skipped_files.append(f"{uploaded_file.name} (unsupported file type)")
            continue

        file_bytes = uploaded_file.getvalue()
        if not file_bytes:
            skipped_files.append(f"{uploaded_file.name} (empty file)")
            continue

        if suffix == ".pdf":
            extracted_documents = _load_pdf(uploaded_file.name, file_bytes)
        else:
            extracted_documents = _load_text(uploaded_file.name, file_bytes, suffix=suffix)

        if extracted_documents:
            documents.extend(extracted_documents)
        else:
            skipped_files.append(f"{uploaded_file.name} (no extractable text)")

    return documents, skipped_files


def _load_pdf(file_name: str, file_bytes: bytes) -> list[Document]:
    pdf_reader = PdfReader(BytesIO(file_bytes))
    documents: list[Document] = []

    for page_number, page in enumerate(pdf_reader.pages, start=1):
        page_text = _clean_text(page.extract_text() or "")
        if not page_text:
            continue

        documents.append(
            Document(
                page_content=page_text,
                metadata={
                    "source": file_name,
                    "page": page_number,
                    "file_type": "pdf",
                },
            )
        )

    return documents


def _load_text(file_name: str, file_bytes: bytes, *, suffix: str) -> list[Document]:
    text = _clean_text(file_bytes.decode("utf-8", errors="ignore"))
    if not text:
        return []

    return [
        Document(
            page_content=text,
            metadata={
                "source": file_name,
                "page": 1,
                "file_type": suffix.lstrip("."),
            },
        )
    ]


def _clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    non_empty_lines = [line for line in lines if line]
    return "\n".join(non_empty_lines)
