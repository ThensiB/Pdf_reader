from __future__ import annotations

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from .config import RAGConfig
from .models import RetrievedChunk


class SemanticVectorIndex:
    def __init__(self, config: RAGConfig) -> None:
        self.config = config
        self._embeddings: OpenAIEmbeddings | None = None
        self._vector_store: FAISS | None = None

    @property
    def ready(self) -> bool:
        return self._vector_store is not None

    def build(self, documents: list[Document]) -> None:
        if not documents:
            raise ValueError("No document chunks were generated for indexing.")

        self._vector_store = FAISS.from_documents(documents, self._get_embeddings())

    def semantic_search(self, query: str, *, k: int | None = None) -> list[RetrievedChunk]:
        vector_store = self._require_vector_store()
        matches = vector_store.similarity_search_with_score(
            query=query,
            k=k or self.config.retrieval_k,
        )
        return [
            RetrievedChunk(content=document.page_content, metadata=document.metadata, score=float(score))
            for document, score in matches
        ]

    def retrieve_for_generation(self, query: str) -> list[RetrievedChunk]:
        vector_store = self._require_vector_store()
        documents = vector_store.max_marginal_relevance_search(
            query=query,
            k=self.config.retrieval_k,
            fetch_k=self.config.retrieval_fetch_k,
        )
        return [
            RetrievedChunk(content=document.page_content, metadata=document.metadata)
            for document in documents
        ]

    def _get_embeddings(self) -> OpenAIEmbeddings:
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(model=self.config.embedding_model)
        return self._embeddings

    def _require_vector_store(self) -> FAISS:
        if self._vector_store is None:
            raise RuntimeError("Build the FAISS index before running retrieval.")
        return self._vector_store
