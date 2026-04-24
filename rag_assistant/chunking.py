from __future__ import annotations

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .config import RAGConfig


def chunk_documents(documents: list[Document], config: RAGConfig) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(documents)

    prepared_chunks: list[Document] = []
    for chunk_index, chunk in enumerate(chunks, start=1):
        chunk.page_content = chunk.page_content.strip()
        if not chunk.page_content:
            continue
        chunk.metadata["chunk_id"] = chunk_index
        prepared_chunks.append(chunk)

    return prepared_chunks
