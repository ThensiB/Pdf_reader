from __future__ import annotations

from typing import Iterable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .config import RAGConfig
from .models import RetrievedChunk, WebSearchResult

REWRITE_SYSTEM_PROMPT = """Rewrite the user's latest question into a standalone semantic search query.
Use the chat history only to resolve references like "it", "they", or "that section".
Do not answer the question. Return only the rewritten query."""


CONTEXT_CHECK_SYSTEM_PROMPT = """You are checking whether the retrieved PDF context is enough to answer the user's question.
Reply with exactly one token:
- ENOUGH_CONTEXT
- INSUFFICIENT_CONTEXT

Choose ENOUGH_CONTEXT only when the retrieved text directly contains enough information to answer the question from the uploaded documents alone.
For summary, overview, notes, recap, or key-points requests about the uploaded PDFs, choose ENOUGH_CONTEXT when the retrieved text gives enough material to summarize the documents, even if it is not exhaustive.
If the retrieved chunks are only loosely related, incomplete, or do not support the answer clearly, reply INSUFFICIENT_CONTEXT."""


ANSWER_SYSTEM_PROMPT = """You are a RAG-based AI document assistant.
Answer only with information supported by the retrieved context.
If the context does not contain the answer, say: I could not find that in the uploaded documents.
Do not invent facts, statistics, citations, or page numbers.
Cite supporting evidence inline with the exact source tokens provided in the context, such as [SOURCE 1].
Prefer a concise answer followed by short supporting bullets when that improves clarity."""


WEB_ANSWER_SYSTEM_PROMPT = """You are a helpful assistant answering with web search results because the uploaded documents did not cover the question.
Use only the provided web results.
Do not invent facts, quotes, or links.
Be clear that this answer came from the web, not from the uploaded documents.
Cite supporting claims inline with the exact source tokens provided in the web context, such as [WEB 1].
Keep the answer concise and beginner-friendly."""


class GroundedResponseGenerator:
    def __init__(self, config: RAGConfig) -> None:
        self.config = config
        self._llm: ChatOpenAI | None = None
        self._judge_llm: ChatOpenAI | None = None

    def rewrite_question(self, question: str, chat_history: list[dict[str, str]]) -> str:
        if not chat_history:
            return question

        response = self._get_llm().invoke(
            [
                SystemMessage(content=REWRITE_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Chat history:\n{self._format_chat_history(chat_history)}\n\n"
                        f"Latest question:\n{question}"
                    )
                ),
            ]
        )
        rewritten_question = _message_to_text(response).strip()
        return rewritten_question or question

    def document_context_is_sufficient(
        self,
        *,
        question: str,
        standalone_question: str,
        retrieved_chunks: list[RetrievedChunk],
        chat_history: list[dict[str, str]],
    ) -> bool:
        if not retrieved_chunks:
            return False

        context = self._format_context(retrieved_chunks)
        history_block = self._format_chat_history(chat_history) or "No previous conversation."

        response = self._get_judge_llm().invoke(
            [
                SystemMessage(content=CONTEXT_CHECK_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Chat history:\n{history_block}\n\n"
                        f"Standalone retrieval question:\n{standalone_question}\n\n"
                        f"Original user question:\n{question}\n\n"
                        f"Retrieved context:\n{context}"
                    )
                ),
            ]
        )
        decision = _message_to_text(response).strip().upper()
        return decision == "ENOUGH_CONTEXT"

    def generate_answer(
        self,
        *,
        question: str,
        standalone_question: str,
        retrieved_chunks: list[RetrievedChunk],
        chat_history: list[dict[str, str]],
    ) -> str:
        if not retrieved_chunks:
            return "I could not find supporting evidence for that in the uploaded documents."

        context = self._format_context(retrieved_chunks)
        history_block = self._format_chat_history(chat_history) or "No previous conversation."

        response = self._get_llm().invoke(
            [
                SystemMessage(content=ANSWER_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Chat history:\n{history_block}\n\n"
                        f"Standalone retrieval question:\n{standalone_question}\n\n"
                        f"Original user question:\n{question}\n\n"
                        f"Retrieved context:\n{context}"
                    )
                ),
            ]
        )
        return _message_to_text(response).strip()

    def generate_web_answer(
        self,
        *,
        question: str,
        standalone_question: str,
        web_results: list[WebSearchResult],
        chat_history: list[dict[str, str]],
    ) -> str:
        if not web_results:
            return "I could not find that in the uploaded documents, and I could not find reliable web results either."

        web_context = self._format_web_context(web_results)
        history_block = self._format_chat_history(chat_history) or "No previous conversation."

        response = self._get_llm().invoke(
            [
                SystemMessage(content=WEB_ANSWER_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Chat history:\n{history_block}\n\n"
                        f"Standalone retrieval question:\n{standalone_question}\n\n"
                        f"Original user question:\n{question}\n\n"
                        f"Web results:\n{web_context}"
                    )
                ),
            ]
        )
        return _message_to_text(response).strip()

    def _get_llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.config.chat_model,
                temperature=self.config.temperature,
            )
        return self._llm

    def _get_judge_llm(self) -> ChatOpenAI:
        if self._judge_llm is None:
            self._judge_llm = ChatOpenAI(
                model=self.config.chat_model,
                temperature=0.0,
            )
        return self._judge_llm

    def _format_chat_history(self, chat_history: list[dict[str, str]]) -> str:
        recent_messages = chat_history[-8:]
        return "\n".join(
            f"{message['role'].capitalize()}: {message['content']}"
            for message in recent_messages
            if message.get("content")
        )

    def _format_context(self, retrieved_chunks: Iterable[RetrievedChunk]) -> str:
        sections: list[str] = []
        for index, chunk in enumerate(retrieved_chunks, start=1):
            sections.append(
                "\n".join(
                    [
                        f"[SOURCE {index}]",
                        f"Location: {chunk.location_label}",
                        "Content:",
                        chunk.content,
                    ]
                )
            )
        return "\n\n".join(sections)

    def _format_web_context(self, web_results: Iterable[WebSearchResult]) -> str:
        sections: list[str] = []
        for index, result in enumerate(web_results, start=1):
            sections.append(
                "\n".join(
                    [
                        f"[WEB {index}]",
                        f"Title: {result.title}",
                        f"URL: {result.url}",
                        f"Snippet: {result.snippet}",
                    ]
                )
            )
        return "\n\n".join(sections)


def _message_to_text(message: AIMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(str(part.get("text", "")))
            else:
                text_parts.append(str(part))
        return "".join(text_parts)
    return str(content)
