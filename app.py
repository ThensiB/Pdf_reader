from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from htmlTemplates import APP_CSS
from rag_assistant import DocumentAssistantPipeline, RAGConfig
from rag_assistant.models import RetrievedChunk


def main() -> None:
    load_dotenv()
    st.set_page_config(
        page_title="RAG-Based AI Document Assistant",
        page_icon=":books:",
        layout="wide",
    )
    st.markdown(APP_CSS, unsafe_allow_html=True)
    _init_session_state()

    _render_header()
    config = _render_sidebar()

    if st.session_state.summary and st.session_state.pipeline:
        _render_summary(st.session_state.summary, st.session_state.pipeline.config)
    else:
        st.info("Upload multiple documents and build the FAISS index to start asking grounded questions.")

    _render_chat_history()
    prompt = st.chat_input("Ask a question about the indexed documents")
    if prompt:
        _handle_user_question(prompt)

    st.divider()
    st.subheader("Semantic Search")
    st.caption("Run FAISS similarity search directly over the embedded chunks to inspect the retrieved evidence.")

    search_query = st.text_input(
        "Search your indexed dataset",
        key="semantic_search_query",
        placeholder="Try a concept, topic, entity, or question",
    )

    if search_query:
        if st.session_state.pipeline and st.session_state.pipeline.ready:
            search_results = st.session_state.pipeline.semantic_search(search_query)
            _render_sources(search_results, show_scores=True)
        else:
            st.warning("Build the index before running semantic search.")


def _init_session_state() -> None:
    st.session_state.setdefault("pipeline", None)
    st.session_state.setdefault("summary", None)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("semantic_search_query", "")


def _render_header() -> None:
    st.markdown(
        """
        <div class="hero-panel">
            <p class="eyebrow">RAG-Based AI Document Assistant</p>
            <h1>Multi-document retrieval with grounded answers</h1>
            <p class="hero-copy">
                End-to-end pipeline: ingestion → chunking & embeddings → FAISS retrieval → response generation.
                Upload a document set, ask questions, inspect retrieved chunks, and trace how the answer was grounded.
            </p>
            <div class="chip-row">
                <span class="chip">FAISS Semantic Search</span>
                <span class="chip">Grounded Prompting</span>
                <span class="chip">Streamlit Interface</span>
                <span class="chip">Modular Pipeline</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> RAGConfig:
    with st.sidebar:
        st.header("Dataset Builder")
        st.caption("Upload multiple `PDF`, `TXT`, or `MD` files and build a FAISS vector index.")

        uploaded_files = st.file_uploader(
            "Choose documents",
            type=["pdf", "txt", "md"],
            accept_multiple_files=True,
        )

        with st.expander("Pipeline Settings", expanded=True):
            chunk_size = st.slider("Chunk size", min_value=300, max_value=1600, value=900, step=100)
            chunk_overlap = st.slider("Chunk overlap", min_value=50, max_value=400, value=180, step=10)
            retrieval_k = st.slider("Top-k chunks", min_value=2, max_value=10, value=6, step=1)
            retrieval_fetch_k = st.slider("Candidate pool", min_value=6, max_value=30, value=20, step=2)
            temperature = st.slider("Answer temperature", min_value=0.0, max_value=0.5, value=0.1, step=0.05)

        build_clicked = st.button("Build / Refresh Index", type="primary", use_container_width=True)
        reset_clicked = st.button("Reset Session", use_container_width=True)

        if reset_clicked:
            st.session_state.pipeline = None
            st.session_state.summary = None
            st.session_state.messages = []
            st.session_state.semantic_search_query = ""
            st.rerun()

        if not os.getenv("OPENAI_API_KEY"):
            st.warning("Set `OPENAI_API_KEY` in `.env` before building the pipeline.")

        config = RAGConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            retrieval_k=retrieval_k,
            retrieval_fetch_k=max(retrieval_fetch_k, retrieval_k),
            temperature=temperature,
        )

        if build_clicked:
            if not uploaded_files:
                st.warning("Upload at least one supported document first.")
            else:
                st.session_state.pipeline = DocumentAssistantPipeline(config)
                with st.spinner("Running ingestion, chunking, embeddings, and FAISS indexing..."):
                    try:
                        st.session_state.summary = st.session_state.pipeline.ingest(uploaded_files)
                    except Exception as exc:
                        st.session_state.pipeline = None
                        st.session_state.summary = None
                        st.error(f"Unable to build the document index: {exc}")
                    else:
                        st.session_state.messages = []
                        st.success("Vector index built successfully. You can start querying now.")

        return config


def _render_summary(summary, config: RAGConfig) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Documents", summary.document_count)
    col2.metric("Records", summary.record_count)
    col3.metric("Chunks Embedded", summary.chunk_count)
    col4.metric("Retriever", f"FAISS / top {config.retrieval_k}")

    st.markdown(
        """
        <div class="stage-panel">
            <div class="stage-card">
                <p class="stage-title">Ingestion</p>
                <p class="stage-body">Multi-document parsing with source and page metadata preserved for each record.</p>
            </div>
            <div class="stage-card">
                <p class="stage-title">Embedding</p>
                <p class="stage-body">Recursive chunking and OpenAI embeddings create a dense representation for each chunk.</p>
            </div>
            <div class="stage-card">
                <p class="stage-title">Retrieval</p>
                <p class="stage-body">FAISS vector indexing powers semantic search and context selection for each user query.</p>
            </div>
            <div class="stage-card">
                <p class="stage-title">Response</p>
                <p class="stage-body">Prompted generation answers only from retrieved evidence and cites source tokens inline.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if summary.sources:
        st.caption(f"Indexed sources: {', '.join(summary.sources)}")
    if summary.skipped_files:
        st.warning(f"Skipped files: {', '.join(summary.skipped_files)}")


def _render_chat_history() -> None:
    st.subheader("Assistant")
    st.caption("Follow-up questions are rewritten into standalone retrieval queries before the answer is generated.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant" and message.get("standalone_question"):
                st.caption(f"Retrieval query: {message['standalone_question']}")

            if message["role"] == "assistant" and message.get("sources"):
                with st.expander("View retrieved source chunks"):
                    _render_sources(message["sources"], show_scores=False)


def _handle_user_question(prompt: str) -> None:
    if not st.session_state.pipeline or not st.session_state.pipeline.ready:
        st.warning("Build the document index before asking a question.")
        return

    chat_history = [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages
    ]
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Retrieving evidence and drafting a grounded answer..."):
        try:
            response = st.session_state.pipeline.answer(prompt, chat_history)
        except Exception as exc:
            st.session_state.messages.pop()
            st.error(f"Unable to answer the question: {exc}")
            return

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response.answer,
            "standalone_question": response.standalone_question,
            "sources": response.sources,
        }
    )
    st.rerun()


def _render_sources(sources: list[RetrievedChunk], *, show_scores: bool) -> None:
    if not sources:
        st.info("No supporting chunks were retrieved.")
        return

    for index, chunk in enumerate(sources, start=1):
        st.markdown(f"**SOURCE {index}** · {chunk.location_label}")
        details = []
        if show_scores and chunk.score is not None:
            details.append(f"FAISS distance: {chunk.score:.4f} (lower is closer)")
        if details:
            st.caption(" | ".join(details))
        st.write(chunk.excerpt())


if __name__ == "__main__":
    main()
