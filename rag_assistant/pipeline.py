from __future__ import annotations

import re

from .chunking import chunk_documents
from .config import RAGConfig
from .generation import GroundedResponseGenerator
from .ingestion import load_documents
from .models import AssistantResponse, IngestionSummary, RetrievedChunk
from .retrieval import SemanticVectorIndex
from .web_search import WebSearchService


class DocumentAssistantPipeline:
    def __init__(self, config: RAGConfig | None = None) -> None:
        self.config = config or RAGConfig()
        self.vector_index = SemanticVectorIndex(self.config)
        self.generator = GroundedResponseGenerator(self.config)
        self.web_search = WebSearchService(self.config)
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
        document_focused_question = _is_document_focused_question(question)
        retrieval_k, retrieval_fetch_k = self._generation_retrieval_settings(question)
        retrieved_chunks = self.vector_index.retrieve_for_generation(
            standalone_question,
            k=retrieval_k,
            fetch_k=retrieval_fetch_k,
        )

        if document_focused_question:
            document_answer = self.generator.generate_answer(
                question=question,
                standalone_question=standalone_question,
                retrieved_chunks=retrieved_chunks,
                chat_history=chat_history,
            )
            return AssistantResponse(
                answer=document_answer,
                standalone_question=standalone_question,
                sources=retrieved_chunks,
            )

        has_enough_document_context = self.generator.document_context_is_sufficient(
            question=question,
            standalone_question=standalone_question,
            retrieved_chunks=retrieved_chunks,
            chat_history=chat_history,
        )

        if not has_enough_document_context and self.config.web_search_enabled:
            web_results = self.web_search.search(standalone_question)
            if web_results:
                web_answer = self.generator.generate_web_answer(
                    question=question,
                    standalone_question=standalone_question,
                    web_results=web_results,
                    chat_history=chat_history,
                )
                return AssistantResponse(
                    answer=web_answer,
                    standalone_question=standalone_question,
                    sources=retrieved_chunks,
                    used_web_search=True,
                    web_sources=web_results,
                )
            return AssistantResponse(
                answer=(
                    "I could not find that in the uploaded documents, and I also could not fetch reliable web "
                    "results right now."
                ),
                standalone_question=standalone_question,
                sources=retrieved_chunks,
            )

        if not has_enough_document_context:
            return AssistantResponse(
                answer="I could not find that in the uploaded documents.",
                standalone_question=standalone_question,
                sources=retrieved_chunks,
            )

        document_answer = self.generator.generate_answer(
            question=question,
            standalone_question=standalone_question,
            retrieved_chunks=retrieved_chunks,
            chat_history=chat_history,
        )

        return AssistantResponse(
            answer=document_answer,
            standalone_question=standalone_question,
            sources=retrieved_chunks,
        )

    def _generation_retrieval_settings(self, question: str) -> tuple[int, int]:
        if not self.summary:
            return self.config.retrieval_k, self.config.retrieval_fetch_k

        if _is_summary_style_question(question):
            summary_k = min(max(self.config.retrieval_k * 2, 8), self.summary.chunk_count)
            summary_fetch_k = min(max(self.config.retrieval_fetch_k, summary_k * 2), self.summary.chunk_count)
            return summary_k, summary_fetch_k

        return self.config.retrieval_k, self.config.retrieval_fetch_k

    def _require_ready(self) -> None:
        if not self.ready:
            raise RuntimeError("Build the FAISS index before querying the assistant.")


def _is_summary_style_question(question: str) -> bool:
    normalized = _normalize_question(question)
    summary_patterns = (
        "summary",
        "summarize",
        "summarise",
        "overview",
        "recap",
        "key points",
        "main points",
        "main ideas",
        "takeaways",
        "study notes",
        "notes",
        "outline",
        "tl dr",
        "tl;dr",
        "brief me",
    )
    return any(pattern in normalized for pattern in summary_patterns)


def _is_document_focused_question(question: str) -> bool:
    normalized = _normalize_question(question)
    document_patterns = (
        "this pdf",
        "the pdf",
        "from the pdf",
        "in the pdf",
        "this document",
        "these documents",
        "uploaded document",
        "uploaded documents",
        "this file",
        "these files",
        "this chapter",
        "this section",
        "compare the documents",
        "compare these documents",
        "compare the uploaded documents",
    )
    return _is_summary_style_question(question) or any(pattern in normalized for pattern in document_patterns)


def _normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", question.lower()).strip()
