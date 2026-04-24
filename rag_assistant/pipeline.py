from __future__ import annotations

from .chunking import chunk_documents
from .config import RAGConfig
from .generation import GroundedResponseGenerator
from .ingestion import load_documents
from .models import AssistantResponse, IngestionSummary, RetrievedChunk
from .retrieval import SemanticVectorIndex


class DocumentAssistantPipeline:
    def __init__(self, config: RAGConfig | None = None) -> None:
        self.config = config or RAGConfig()
        self.vector_index = SemanticVectorIndex(self.config)
        self.generator = GroundedResponseGenerator(self.config)
        self.summary: IngestionSummary | None = None

    @property
    def ready(self) -> bool:
        return self.summary is not None and self.vector_index.ready

    def ingest(self, uploaded_files) -> IngestionSummary:
        documents, skipped_files = load_documents(uploaded_files)
        if not documents:
            raise ValueError("No readable content was found in the uploaded files.")

        chunks = chunk_documents(documents, self.config)
        if not chunks:
            raise ValueError("The documents were loaded, but chunking produced no usable text.")

        self.vector_index.build(chunks)

        sources = sorted({str(document.metadata.get("source", "Unknown source")) for document in documents})
        self.summary = IngestionSummary(
            document_count=len(sources),
            record_count=len(documents),
            chunk_count=len(chunks),
            skipped_files=skipped_files,
            sources=sources,
        )
        return self.summary

    def semantic_search(self, query: str, *, k: int | None = None) -> list[RetrievedChunk]:
        self._require_ready()
        return self.vector_index.semantic_search(query, k=k)

    def answer(self, question: str, chat_history: list[dict[str, str]]) -> AssistantResponse:
        self._require_ready()
        standalone_question = self.generator.rewrite_question(question, chat_history)
        retrieved_chunks = self.vector_index.retrieve_for_generation(standalone_question)
        answer = self.generator.generate_answer(
            question=question,
            standalone_question=standalone_question,
            retrieved_chunks=retrieved_chunks,
            chat_history=chat_history,
        )
        return AssistantResponse(
            answer=answer,
            standalone_question=standalone_question,
            sources=retrieved_chunks,
        )

    def _require_ready(self) -> None:
        if not self.ready:
            raise RuntimeError("Build the FAISS index before querying the assistant.")
