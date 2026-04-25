from dataclasses import dataclass


@dataclass(slots=True)
class RAGConfig:
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    temperature: float = 0.1
    chunk_size: int = 900
    chunk_overlap: int = 180
    retrieval_k: int = 6
    retrieval_fetch_k: int = 20
    web_search_enabled: bool = True
    web_search_results: int = 5
    web_search_timeout_seconds: int = 10
