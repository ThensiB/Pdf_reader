from __future__ import annotations

import html
import os
import random

import streamlit as st
from dotenv import load_dotenv

from htmlTemplates import APP_CSS
from rag_assistant import DocumentAssistantPipeline, RAGConfig

SUGGESTED_QUESTIONS = [
    "Give me a quick summary of the main ideas.",
    "What are the most important definitions or formulas?",
    "Turn this into study notes I can revise from.",
    "Compare the uploaded documents and highlight differences.",
]

THINKING_MESSAGES = [
    "Reading between the lines and checking your documents...",
    "Looking through the indexed chunks like a study buddy...",
    "Pulling the best document context together for you...",
    "Checking whether your PDFs cover this before looking wider...",
]


def main() -> None:
    load_dotenv()
    st.set_page_config(
        page_title="Ask Your PDF Anything",
        page_icon=":books:",
        layout="wide",
    )
    st.markdown(APP_CSS, unsafe_allow_html=True)
    _init_session_state()

    config = _render_sidebar()
    _render_hero()
    _render_upload_workspace(config)

    if st.session_state.summary and st.session_state.pipeline:
        _render_summary(st.session_state.summary, st.session_state.pipeline.config)
    _render_chat_panel()


def _init_session_state() -> None:
    st.session_state.setdefault("pipeline", None)
    st.session_state.setdefault("summary", None)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("uploader_version", 0)


def _render_sidebar() -> RAGConfig:
    with st.sidebar:
        st.markdown("### Tune Your Assistant")

        with st.expander("Advanced settings", expanded=True):
            chunk_size = st.slider("Chunk size", min_value=300, max_value=1600, value=900, step=100)
            chunk_overlap = st.slider("Chunk overlap", min_value=50, max_value=400, value=180, step=10)
            retrieval_k = st.slider("Top-k chunks", min_value=2, max_value=10, value=6, step=1)
            retrieval_fetch_k = st.slider("Candidate pool", min_value=6, max_value=30, value=20, step=2)
            temperature = st.slider("Answer temperature", min_value=0.0, max_value=0.5, value=0.1, step=0.05)

        if st.session_state.summary:
            st.markdown("### Live status")
            st.success(
                f"Ready with {st.session_state.summary.document_count} document(s) "
                f"and {st.session_state.summary.chunk_count} chunks."
            )
            st.caption("If the PDF does not cover a question, the assistant can fall back to web search with links.")
        else:
            st.info("Upload documents in the main workspace to get started.")

        if not os.getenv("OPENAI_API_KEY"):
            st.warning("Add `OPENAI_API_KEY` to `.env` before building the assistant.")

        if st.button("Reset chat and index", use_container_width=True):
            st.session_state.pipeline = None
            st.session_state.summary = None
            st.session_state.messages = []
            st.rerun()

        return RAGConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            retrieval_k=retrieval_k,
            retrieval_fetch_k=max(retrieval_fetch_k, retrieval_k),
            temperature=temperature,
        )


def _render_hero() -> None:
    st.markdown(
        """
        <div class="hero-panel">
            <p class="eyebrow">Study Companion</p>
            <h1>Ask your PDF anything 📚</h1>
            <p class="hero-copy">
                Upload one or more PDFs, build a searchable study buddy, and ask questions.
                If the answer is not in your documents, the assistant can look it up online and show source links.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_upload_workspace(config: RAGConfig) -> None:
    st.markdown(
        """
        <div class="section-intro">
            <h3>Upload your study material</h3>
            <p>Drag and drop one or more PDFs, then build your companion when you're ready.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_files = st.file_uploader(
        "Drop PDFs, TXT, or MD files here",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        help="You can upload multiple files at once and ask cross-document questions.",
        key=f"uploaded_docs_{st.session_state.uploader_version}",
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) selected and ready to process.")
        _render_selected_files(uploaded_files)
    else:
        st.markdown(
            """
            <div class="empty-state-card">
                <h4>No files uploaded yet</h4>
                <p>Start with a lecture slide deck, textbook chapter, report, or research paper.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    button_label = "✨ Build my study buddy" if not st.session_state.summary else "🔄 Rebuild with these files"
    build_col, clear_col = st.columns(2)

    with build_col:
        if st.button(button_label, type="primary", use_container_width=True):
            _build_pipeline(uploaded_files, config)

    with clear_col:
        if st.button("🗑️ Clear uploaded PDFs", use_container_width=True):
            _clear_uploaded_documents()


def _build_pipeline(uploaded_files, config: RAGConfig) -> None:
    if not uploaded_files:
        st.error("Please upload at least one PDF or text document first.")
        return

    if not os.getenv("OPENAI_API_KEY"):
        st.error("I need `OPENAI_API_KEY` in `.env` before I can process your documents.")
        return

    st.session_state.pipeline = DocumentAssistantPipeline(config)

    # Keep the original backend flow intact: the UI still funnels processing through pipeline.ingest().
    with st.status("Creating your study-ready document assistant...", expanded=True) as status:
        status.write("Reading the uploaded files and extracting text.")

        try:
            st.session_state.summary = st.session_state.pipeline.ingest(uploaded_files)
        except Exception as exc:
            st.session_state.pipeline = None
            st.session_state.summary = None
            status.update(label="I ran into a problem while building the index.", state="error", expanded=True)
            st.error(f"Something went wrong while processing the documents: {exc}")
        else:
            st.session_state.messages = []
            status.update(label="Your study buddy is ready to chat!", state="complete", expanded=False)
            st.success("Success! Your documents are ready for questions.")


def _clear_uploaded_documents() -> None:
    # Streamlit file uploaders are cleared by changing their widget key.
    st.session_state.pipeline = None
    st.session_state.summary = None
    st.session_state.messages = []
    st.session_state.uploader_version += 1
    st.rerun()


def _render_selected_files(uploaded_files) -> None:
    pills = "".join(
        f"<span class='file-pill'>📎 {html.escape(uploaded_file.name)}</span>"
        for uploaded_file in uploaded_files
    )
    st.markdown(f"<div class='file-pill-row'>{pills}</div>", unsafe_allow_html=True)


def _render_summary(summary, config: RAGConfig) -> None:
    st.markdown(
        """
        <div class="ready-banner">
            <div>
                <p class="card-kicker">Step 2</p>
                <h3>Your companion is warmed up and ready</h3>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if summary.sources:
        st.caption(f"Indexed sources: {', '.join(summary.sources)}")
    if summary.skipped_files:
        st.warning(f"Some files were skipped: {', '.join(summary.skipped_files)}")


def _render_chat_panel() -> None:
    ready = bool(st.session_state.pipeline and st.session_state.pipeline.ready)
    st.markdown(
        """
        <div class="section-intro compact chat-section">
            <h3>Chat with your PDF</h3>
            <p>Ask a question and get an answer from the documents.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if ready:
        _render_suggested_questions()

    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="🧠"):
            if ready:
                st.markdown(
                    "Hi! I'm your PDF study buddy. Ask your PDF anything, or tap one of the suggested questions "
                    "to kick things off."
                )
            else:
                st.markdown(
                    "Hi! Upload your documents first, then I'll help you summarize, explain tricky sections, "
                    "compare files, and find supporting evidence."
                )

    for message in st.session_state.messages:
        avatar = "🧠" if message["role"] == "assistant" else "🧑"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

            if message["role"] == "assistant" and message.get("standalone_question"):
                st.caption(f"Search query used behind the scenes: {message['standalone_question']}")

            if message["role"] == "assistant" and message.get("used_web_search"):
                st.caption("I could not find this in the uploaded documents, so I checked the web.")
                _render_web_sources(message.get("web_sources", []))

            if (
                message["role"] == "assistant"
                and message.get("sources")
                and not message.get("used_web_search")
            ):
                with st.expander("See the source passages behind this answer"):
                    _render_sources(message["sources"], show_scores=False)

    prompt = st.chat_input("Ask your PDF anything...", disabled=not ready)
    if prompt:
        _handle_user_question(prompt)


def _render_suggested_questions() -> None:
    st.markdown("##### Need inspiration? Try one of these")

    # These chips still route through the same backend handler as typed chat, so the retrieval flow stays unchanged.
    columns = st.columns(2)
    for index, question in enumerate(SUGGESTED_QUESTIONS):
        with columns[index % 2]:
            if st.button(question, key=f"suggested_question_{index}", use_container_width=True):
                _handle_user_question(question)


def _handle_user_question(prompt: str) -> None:
    if not st.session_state.pipeline or not st.session_state.pipeline.ready:
        st.warning("Build the document index before asking a question.")
        return

    chat_history = [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages
    ]
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner(random.choice(THINKING_MESSAGES)):
        try:
            response = st.session_state.pipeline.answer(prompt, chat_history)
        except Exception as exc:
            st.session_state.messages.pop()
            st.error(f"I couldn't answer that just yet: {exc}")
            return

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response.answer,
            "standalone_question": response.standalone_question,
            "sources": response.sources,
            "used_web_search": response.used_web_search,
            "web_sources": response.web_sources,
        }
    )
    st.rerun()


def _render_sources(sources, *, show_scores: bool) -> None:
    if not sources:
        st.info("No supporting chunks were retrieved.")
        return

    for index, chunk in enumerate(sources, start=1):
        meta_parts = [chunk.location_label]
        if show_scores and chunk.score is not None:
            meta_parts.append(f"FAISS distance {chunk.score:.4f} (lower = closer match)")

        st.markdown(
            f"""
            <div class="source-card">
                <p class="source-tag">SOURCE {index}</p>
                <h4>{html.escape(chunk.location_label)}</h4>
                <p class="source-meta">{html.escape(" | ".join(meta_parts))}</p>
                <p class="source-snippet">{html.escape(chunk.excerpt())}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_web_sources(web_sources) -> None:
    if not web_sources:
        return

    for result in web_sources:
        st.markdown(f"- [{result.title}]({result.url})")
        if result.snippet:
            st.caption(f"{result.domain} | {result.snippet}")


if __name__ == "__main__":
    main()
