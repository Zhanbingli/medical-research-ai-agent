"""
CSS styles and UI constants.
"""

CUSTOM_CSS = """
<style>
    /* Global Settings */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Color Variables */
    :root {
        --primary-color: #2563EB;
        --secondary-color: #64748B;
        --background-color: #F8FAFC;
        --card-bg: #FFFFFF;
        --text-color: #1E293B;
        --border-color: #E2E8F0;
    }

    /* Main Container */
    .stApp {
        background-color: var(--background-color);
    }

    /* Header Styling */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }

    .subtitle {
        font-size: 1.1rem;
        color: var(--secondary-color);
        margin-bottom: 2rem;
    }

    /* Card Styling */
    .article-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .article-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        transform: translateY(-2px);
        border-color: var(--primary-color);
    }

    .article-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-color);
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }

    .article-meta {
        font-size: 0.875rem;
        color: var(--secondary-color);
        margin-bottom: 1rem;
        display: flex;
        gap: 1rem;
        align-items: center;
    }

    /* Badges */
    .ai-provider-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.025em;
        text-transform: uppercase;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    .claude-badge { background-color: #F6EBE7; color: #D97757; border: 1px solid #F0D0C6; }
    .kimi-badge { background-color: #EBF5FF; color: #4285F4; border: 1px solid #BFDBFE; }
    .qwen-badge { background-color: #FFF7ED; color: #EA580C; border: 1px solid #FED7AA; }

    /* Custom Buttons */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }

    .stButton button:hover {
        transform: translateY(-1px);
    }

    /* Expander Styling */
    .streamlit-expanderHeader {
        background-color: transparent;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 500;
    }

    /* Divider */
    hr {
        margin: 1.5rem 0;
        border-color: var(--border-color);
    }
</style>
"""

PROVIDER_LABELS = {
    "claude": "Claude (Anthropic)",
    "kimi": "Kimi (月之暗面)",
    "qwen": "Qwen (通义千问)"
}
