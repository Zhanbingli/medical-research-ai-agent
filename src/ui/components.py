"""
Reusable UI components.
"""
import streamlit as st
import time

def toast_error(message: str):
    """Show a quick user-facing error toast."""
    st.toast(f"❌ {message}", icon="⚠️")


def get_provider_badge(provider: str) -> str:
    """Get HTML badge for AI provider."""
    badges = {
        "claude": '<span class="ai-provider-badge claude-badge">Claude</span>',
        "kimi": '<span class="ai-provider-badge kimi-badge">Kimi</span>',
        "qwen": '<span class="ai-provider-badge qwen-badge">Qwen</span>'
    }
    return badges.get(provider.lower(), f'<span class="ai-provider-badge">{provider}</span>')


def display_article(article, idx, analyzer=None, selected_provider=None):
    """Display a single article with analysis options."""
    # Start card container
    with st.container():
        # Article Header (Title & Meta) wrapped in a custom styled div for the "Card" look
        st.markdown(f"""
        <div class="article-card">
            <div class="article-title">{article['title']}</div>
            <div class="article-meta">
                <span>👥 {", ".join(article.get('authors', [])[:3])}{" et al." if len(article.get('authors', [])) > 3 else ""}</span>
                <span>•</span>
                <span>📅 {article.get('pub_date', 'N/A').split()[0]}</span>
                <span>•</span>
                <span>📰 {article.get('journal', 'N/A')}</span>
            </div>
            <div style="margin-top: 1rem;">
                <a href="https://pubmed.ncbi.nlm.nih.gov/{article.get('pmid', '')}/" target="_blank" style="text-decoration: none; color: var(--primary-color); font-weight: 500; font-size: 0.9rem;">
                    View on PubMed ↗
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])

        # We moved the title/link into the HTML card above for better styling control.
        # Now we just handle the Abstract and Actions below the "Card Header".

        # Abstract Expander
        with st.expander("📝 Show Abstract", expanded=False):
            st.markdown(f"<div style='color: var(--text-color); line-height: 1.6;'>{article.get('abstract', 'No abstract available')}</div>", unsafe_allow_html=True)

            # Keywords
            if article.get('keywords'):
                st.markdown(f"**Keywords:** {', '.join(article.get('keywords', [])[:5])}")

        # AI Actions
        if analyzer:
            cols = st.columns(4)

            with cols[0]:
                if st.button(f"✨ Summarize", key=f"summary_{idx}", help="Generate a detailed summary"):
                    try:
                        with st.spinner(f"Summarizing with {selected_provider.upper()}..."):
                            summary = analyzer.summarize_article(
                                article, style="detailed", provider=selected_provider
                            )
                        st.success("Summary Generated")
                        st.info(summary)
                    except Exception as e:
                        toast_error(f"Summary failed: {e}")

            with cols[1]:
                if st.button(f"🔑 Key Points", key=f"keypoints_{idx}", help="Extract key findings"):
                    try:
                        with st.spinner(f"Extracting points with {selected_provider.upper()}..."):
                            points = analyzer.extract_key_points(article, provider=selected_provider)
                        st.success("Key Points Extracted")
                        st.info(points)
                    except Exception as e:
                        toast_error(f"Extraction failed: {e}")

        st.markdown("<br>", unsafe_allow_html=True) # Spacer
