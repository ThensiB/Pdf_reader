# RAG-Based AI Document Assistant

This project implements an end-to-end Retrieval-Augmented Generation workflow for multi-document datasets. It ingests uploaded files, chunks the extracted text, generates embeddings, indexes the chunks in FAISS, retrieves the most relevant context, and produces grounded answers through a Streamlit interface.

## Features

- End-to-end modular RAG pipeline: ingestion → embedding → retrieval → response
- Multi-document ingestion with source and page metadata
- FAISS vector indexing for semantic search and context-aware question answering
- Grounded prompting with source-token citations to reduce hallucinations
- Automatic web-search fallback when the PDFs do not contain the answer, including source links
- Streamlit interface for interactive querying and source inspection


## Run Locally

1. Create or activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add your OpenAI API key to `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

4. Start the Streamlit app:

```bash
streamlit run app.py
```

## Architecture

- `ingestion.py` loads PDF, TXT, and Markdown documents and preserves metadata.
- `chunking.py` applies recursive chunking for dense retrieval.
- `retrieval.py` builds and queries a FAISS vector index.
- `generation.py` rewrites follow-up questions, applies grounded prompts, and generates cited answers.
- `web_search.py` fetches fallback web results and supplies source links when the document set is insufficient.
- `pipeline.py` orchestrates the full workflow behind the Streamlit interface.
