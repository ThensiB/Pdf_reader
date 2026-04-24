APP_CSS = """
<style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(232, 245, 255, 0.95), transparent 30%),
            radial-gradient(circle at top right, rgba(255, 239, 224, 0.9), transparent 35%),
            linear-gradient(180deg, #f8fafc 0%, #eef3f8 100%);
        color: #122033;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f3f7fb 100%);
        border-right: 1px solid rgba(18, 32, 51, 0.08);
    }

    .hero-panel {
        padding: 1.4rem 1.5rem;
        border-radius: 22px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(239, 246, 255, 0.92));
        border: 1px solid rgba(18, 32, 51, 0.08);
        box-shadow: 0 18px 42px rgba(41, 65, 96, 0.08);
        margin-bottom: 1.25rem;
    }

    .eyebrow {
        margin: 0;
        color: #0f6c6d;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .hero-panel h1 {
        margin: 0.35rem 0 0.6rem;
        color: #0f172a;
        font-size: 2.1rem;
        line-height: 1.15;
    }

    .hero-copy {
        margin: 0;
        color: #334155;
        font-size: 1rem;
        line-height: 1.65;
        max-width: 58rem;
    }

    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 1rem;
    }

    .chip {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 0.35rem 0.8rem;
        background: rgba(15, 108, 109, 0.08);
        color: #0f6c6d;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .stage-panel {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.8rem;
        margin: 1rem 0 0.2rem;
    }

    .stage-card {
        padding: 1rem;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(18, 32, 51, 0.07);
        box-shadow: 0 10px 24px rgba(41, 65, 96, 0.06);
    }

    .stage-title {
        margin: 0 0 0.3rem;
        color: #0f172a;
        font-size: 0.95rem;
        font-weight: 700;
    }

    .stage-body {
        margin: 0;
        color: #475569;
        font-size: 0.9rem;
        line-height: 1.55;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid rgba(18, 32, 51, 0.07);
        padding: 0.85rem 0.95rem;
        border-radius: 18px;
        box-shadow: 0 10px 24px rgba(41, 65, 96, 0.06);
    }
</style>
"""
