APP_CSS = """
<style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(255, 248, 237, 0.9), transparent 28%),
            radial-gradient(circle at top right, rgba(220, 252, 231, 0.75), transparent 30%),
            linear-gradient(180deg, #fffdf8 0%, #f6f8fc 100%);
        color: #1f2937;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f7fafc 100%);
        border-right: 1px solid rgba(15, 23, 42, 0.08);
    }

    h1, h2, h3, h4 {
        letter-spacing: -0.02em;
    }

    .hero-panel,
    .ready-banner,
    .empty-state-card,
    .source-card {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(15, 23, 42, 0.08);
        box-shadow: 0 16px 38px rgba(15, 23, 42, 0.07);
    }

    .hero-panel {
        padding: 1.55rem 1.6rem;
        border-radius: 28px;
        background:
            radial-gradient(circle at top right, rgba(251, 191, 36, 0.16), transparent 28%),
            linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(240, 249, 255, 0.96));
        margin-bottom: 1.25rem;
    }

    .eyebrow,
    .card-kicker,
    .source-tag {
        margin: 0;
        color: #0f766e;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .hero-panel h1 {
        margin: 0.35rem 0 0.7rem;
        color: #0f172a;
        font-size: 2.85rem;
        line-height: 1.02;
    }

    .hero-copy {
        margin: 0;
        color: #475569;
        font-size: 1.05rem;
        line-height: 1.7;
        max-width: 58rem;
    }

    .chip-row,
    .file-pill-row,
    .ready-pill-stack {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        margin-top: 1rem;
    }

    .chip,
    .file-pill,
    .ready-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        border-radius: 999px;
        padding: 0.42rem 0.85rem;
        font-size: 0.9rem;
        font-weight: 600;
    }

    .chip {
        background: rgba(13, 148, 136, 0.1);
        color: #0f766e;
    }

    .file-pill {
        background: rgba(59, 130, 246, 0.08);
        color: #1d4ed8;
        margin-top: 0.85rem;
    }

    .ready-pill {
        background: rgba(245, 158, 11, 0.11);
        color: #9a6700;
    }

    .ready-banner h3,
    .section-intro h3,
    .empty-state-card h4,
    .source-card h4 {
        margin: 0.35rem 0 0.55rem;
        color: #0f172a;
    }

    .section-intro {
        margin: 1rem 0 0.8rem;
    }

    .section-intro p {
        margin: 0;
        color: #64748b;
        line-height: 1.6;
    }

    .section-intro.compact {
        margin-top: 1.2rem;
    }

    .section-intro.chat-section {
        margin-top: 1.5rem;
    }

    div[data-testid="stFileUploader"] {
        margin-top: 0.35rem;
    }

    [data-testid="stFileUploaderDropzone"] {
        border: 2px dashed rgba(13, 148, 136, 0.32);
        border-radius: 24px;
        background:
            radial-gradient(circle at top right, rgba(253, 224, 71, 0.16), transparent 28%),
            linear-gradient(180deg, rgba(240, 253, 250, 0.92), rgba(255, 255, 255, 0.95));
        padding: 1.05rem;
        transition: all 0.2s ease;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: rgba(13, 148, 136, 0.65);
        box-shadow: 0 14px 34px rgba(13, 148, 136, 0.08);
    }

    [data-testid="stFileUploaderDropzoneInstructions"] > div {
        color: #0f172a;
        font-weight: 600;
    }

    .empty-state-card {
        padding: 1.2rem 1.15rem;
        border-radius: 22px;
        margin-top: 0.75rem;
        text-align: left;
    }

    .empty-state-card p {
        margin: 0;
        color: #64748b;
        line-height: 1.65;
    }

    .empty-emoji {
        font-size: 1.55rem;
        margin-bottom: 0.45rem !important;
    }

    .ready-banner {
        margin-top: 1.1rem;
        border-radius: 26px;
        padding: 1.25rem 1.3rem;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 1rem;
    }

    .ready-banner p {
        margin: 0;
        color: #475569;
        line-height: 1.65;
        max-width: 42rem;
    }

    .stage-panel {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
        gap: 0.85rem;
        margin: 1rem 0 0.25rem;
    }

    .stage-card {
        padding: 1rem;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(15, 23, 42, 0.08);
        box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
    }

    .stage-title {
        margin: 0 0 0.35rem;
        color: #0f172a;
        font-size: 0.98rem;
        font-weight: 700;
    }

    .stage-body {
        margin: 0;
        color: #64748b;
        line-height: 1.58;
        font-size: 0.92rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(15, 23, 42, 0.08);
        padding: 0.9rem 1rem;
        border-radius: 20px;
        box-shadow: 0 14px 30px rgba(15, 23, 42, 0.06);
    }

    div[data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.86);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 22px;
        padding: 0.4rem 0.25rem;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
        margin-bottom: 0.75rem;
    }

    div[data-testid="stChatInput"] {
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 24px;
        box-shadow: 0 16px 32px rgba(15, 23, 42, 0.06);
        padding: 0.25rem 0.35rem;
    }

    div[data-testid="stTextInputRootElement"] > div,
    div[data-baseweb="input"] {
        border-radius: 18px !important;
    }

    .source-card {
        border-radius: 22px;
        padding: 1rem 1rem 0.95rem;
        margin-bottom: 0.85rem;
    }

    .source-meta,
    .source-snippet {
        margin: 0;
        color: #64748b;
        line-height: 1.65;
    }

    .source-snippet {
        margin-top: 0.55rem;
        color: #334155;
    }

    button[kind="primary"] {
        border-radius: 16px;
        border: none;
        background: linear-gradient(135deg, #0f766e, #14b8a6);
        box-shadow: 0 14px 28px rgba(13, 148, 136, 0.22);
    }

    button[kind="secondary"] {
        border-radius: 999px;
        border: 1px solid rgba(15, 23, 42, 0.08);
        background: rgba(255, 255, 255, 0.88);
    }

    div[data-testid="stStatusWidget"] {
        border-radius: 22px;
        border: 1px solid rgba(15, 23, 42, 0.08);
        box-shadow: 0 16px 34px rgba(15, 23, 42, 0.06);
    }

    @media (max-width: 900px) {
        .block-container {
            padding-top: 1.2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .hero-panel h1 {
            font-size: 2.15rem;
        }

        .hero-copy {
            font-size: 0.98rem;
        }

        .ready-banner {
            padding: 1.05rem 1rem;
        }
    }
</style>
"""
