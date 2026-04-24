from __future__ import annotations

from typing import Iterable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .config import RAGConfig
from .models import RetrievedChunk


REWRITE_SYSTEM_PROMPT = """Rewrite the user's latest question into a standalone semantic search query.
Use the chat history only to resolve references like "it", "they", or "that section".
Do not answer the question. Return only the rewritten query."""


ANSWER_SYSTEM_PROMPT = """You are a RAG-based AI document assistant.
Answer only with information supported by the retrieved context.
If the context does not contain the answer, say that you could not find it in the uploaded documents.
Do not invent facts, statistics, citations, or page numbers.
Cite supporting evidence inline with the exact source tokens provided in the context, such as [SOURCE 1].
Prefer a concise answer followed by short supporting bullets when that improves clarity."""


class GroundedResponseGenerator:
    def __init__(self, config: RAGConfig) -> None:
        self.config = config
        self._llm: ChatOpenAI | None = None

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

    def _get_llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.config.chat_model,
                temperature=self.config.temperature,
            )
        return self._llm

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
