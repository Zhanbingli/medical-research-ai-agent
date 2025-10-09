"""
Medical Literature Search and Analysis - Multi-AI Streamlit Application
Support for Claude, Kimi (月之暗面), and Qwen (通义千问)
"""
import streamlit as st
import os
from dotenv import load_dotenv
import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_sources import PubMedClient
from src.agents import MultiAIAnalyzer

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Medical Literature Agent - Multi-AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .ai-provider-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        font-weight: bold;
        margin-left: 0.5rem;
    }
    .claude-badge { background-color: #D97757; color: white; }
    .kimi-badge { background-color: #4285F4; color: white; }
    .qwen-badge { background-color: #FF6A00; color: white; }
</style>
""", unsafe_allow_html=True)


def get_provider_badge(provider: str) -> str:
    """Get HTML badge for AI provider."""
    badges = {
        "claude": '<span class="ai-provider-badge claude-badge">Claude</span>',
        "kimi": '<span class="ai-provider-badge kimi-badge">Kimi</span>',
        "qwen": '<span class="ai-provider-badge qwen-badge">Qwen</span>'
    }
    return badges.get(provider.lower(), f'<span class="ai-provider-badge">{provider}</span>')


def initialize_clients():
    """Initialize PubMed and AI clients."""
    try:
        pubmed = PubMedClient(email=os.getenv("PUBMED_EMAIL"))
        analyzer = MultiAIAnalyzer()
        return pubmed, analyzer
    except ValueError as e:
        st.error(f"Configuration Error: {e}")
        st.info("Please set at least one AI API key in your .env file")
        return None, None


def display_article(article, idx, analyzer=None, selected_provider=None):
    """Display a single article with analysis options."""
    with st.container():
        st.markdown(f"### 📄 Article {idx + 1}")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{article['title']}**")
            authors = ", ".join(article.get('authors', [])[:5])
            if len(article.get('authors', [])) > 5:
                authors += " et al."
            st.caption(f"👥 {authors}")
            st.caption(f"📰 {article.get('journal', 'N/A')} | 📅 {article.get('pub_date', 'N/A')}")

        with col2:
            pmid = article.get('pmid', '')
            if pmid:
                st.link_button(
                    "View on PubMed",
                    f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    use_container_width=True
                )

        # Abstract
        with st.expander("📝 Abstract", expanded=False):
            abstract = article.get('abstract', 'No abstract available')
            st.write(abstract)

        # Keywords and MeSH terms
        col1, col2 = st.columns(2)
        with col1:
            keywords = article.get('keywords', [])
            if keywords:
                st.markdown("**Keywords:** " + ", ".join(keywords[:5]))

        with col2:
            mesh_terms = article.get('mesh_terms', [])
            if mesh_terms:
                st.markdown("**MeSH Terms:** " + ", ".join(mesh_terms[:5]))

        # AI Analysis buttons
        if analyzer:
            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"🤖 AI Summary", key=f"summary_{idx}"):
                    with st.spinner(f"Generating summary with {selected_provider.upper()}..."):
                        start_time = time.time()
                        summary = analyzer.summarize_article(
                            article, style="detailed", provider=selected_provider
                        )
                        elapsed = time.time() - start_time

                    st.info(summary)
                    st.caption(f"⏱️ Generated in {elapsed:.2f}s using {selected_provider.upper()}")

            with col2:
                if st.button(f"🔑 Key Points", key=f"keypoints_{idx}"):
                    with st.spinner(f"Extracting key points with {selected_provider.upper()}..."):
                        start_time = time.time()
                        key_points = analyzer.extract_key_points(article, provider=selected_provider)
                        elapsed = time.time() - start_time

                    st.info(key_points)
                    st.caption(f"⏱️ Generated in {elapsed:.2f}s using {selected_provider.upper()}")

        st.divider()


def main():
    """Main application."""
    # Header
    st.markdown('<p class="main-header">📚 Medical Literature Agent - Multi-AI</p>', unsafe_allow_html=True)
    st.markdown("Search PubMed and analyze with **Claude**, **Kimi (月之暗面)**, or **Qwen (通义千问)**")

    # Initialize clients
    pubmed, analyzer = initialize_clients()

    if not pubmed or not analyzer:
        st.stop()

    # Get available AI providers
    available_providers = analyzer.get_available_providers()

    if not available_providers:
        st.error("No AI providers available. Please configure API keys in .env")
        st.stop()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # AI Provider Selection
        st.subheader("🤖 AI Provider")

        provider_labels = {
            "claude": "Claude (Anthropic)",
            "kimi": "Kimi (月之暗面)",
            "qwen": "Qwen (通义千问)"
        }

        display_providers = [provider_labels.get(p, p) for p in available_providers]

        selected_display = st.selectbox(
            "Select AI Model",
            display_providers,
            help="Choose which AI model to use for analysis"
        )

        # Map back to provider key
        selected_provider = available_providers[display_providers.index(selected_display)]

        # Show provider info
        provider_info = analyzer.get_provider_info(selected_provider)
        with st.expander("ℹ️ Provider Info", expanded=False):
            st.json(provider_info)

        st.divider()

        # Search Settings
        st.subheader("🔍 Search Settings")

        search_query = st.text_input(
            "Search Query",
            placeholder="e.g., diabetes machine learning",
            help="Use PubMed search syntax for advanced queries"
        )

        max_results = st.slider(
            "Number of Results",
            min_value=1,
            max_value=20,
            value=5,
            help="Maximum number of articles to retrieve"
        )

        sort_order = st.selectbox(
            "Sort By",
            ["relevance", "pub_date"],
            help="Sort results by relevance or publication date"
        )

        # Date range
        st.subheader("📅 Date Range")
        use_date_range = st.checkbox("Filter by date range")

        min_date = None
        max_date = None

        if use_date_range:
            col1, col2 = st.columns(2)
            with col1:
                min_year = st.number_input("From Year", min_value=1900, max_value=2025, value=2020)
            with col2:
                max_year = st.number_input("To Year", min_value=1900, max_value=2025, value=2025)

            min_date = f"{min_year}/01/01"
            max_date = f"{max_year}/12/31"

        search_button = st.button("🔍 Search", type="primary", use_container_width=True)

    # Main content area
    if search_button:
        if not search_query:
            st.warning("Please enter a search query")
            st.stop()

        with st.spinner(f"Searching PubMed for '{search_query}'..."):
            articles = pubmed.search_and_fetch(
                query=search_query,
                max_results=max_results,
                sort=sort_order,
                min_date=min_date,
                max_date=max_date
            )

        if not articles:
            st.warning("No articles found. Try a different query.")
            st.stop()

        # Store in session state
        st.session_state['articles'] = articles
        st.session_state['search_query'] = search_query

    # Display results
    if 'articles' in st.session_state:
        articles = st.session_state['articles']
        search_query = st.session_state.get('search_query', '')

        st.success(f"Found {len(articles)} articles for: **{search_query}**")
        st.markdown(f"Using AI: {get_provider_badge(selected_provider)}", unsafe_allow_html=True)

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📑 Articles", "📊 Synthesis", "💬 Q&A", "🔬 AI Comparison"])

        with tab1:
            st.subheader("Search Results")
            for idx, article in enumerate(articles):
                display_article(article, idx, analyzer, selected_provider)

        with tab2:
            st.subheader("AI Synthesis of Multiple Articles")
            st.markdown("Generate a comprehensive analysis combining insights from all retrieved articles.")

            research_question = st.text_area(
                "Specific Research Question (Optional)",
                placeholder="e.g., What are the most effective treatments?",
                help="Leave empty for general synthesis"
            )

            if st.button("🧠 Generate Synthesis", type="primary"):
                with st.spinner(f"Analyzing articles with {selected_provider.upper()}..."):
                    start_time = time.time()
                    synthesis = analyzer.synthesize_multiple(
                        articles,
                        research_question if research_question else None,
                        provider=selected_provider
                    )
                    elapsed = time.time() - start_time

                st.markdown("### 📝 Synthesis Results")
                st.markdown(synthesis)
                st.caption(f"⏱️ Generated in {elapsed:.2f}s using {selected_provider.upper()}")

        with tab3:
            st.subheader("Ask Questions About the Literature")
            st.markdown("Ask specific questions and get AI-powered answers based on the retrieved articles.")

            question = st.text_input(
                "Your Question",
                placeholder="e.g., What biomarkers were identified in these studies?"
            )

            if st.button("❓ Get Answer", type="primary") and question:
                with st.spinner(f"Finding answer with {selected_provider.upper()}..."):
                    start_time = time.time()
                    answer = analyzer.answer_question(articles, question, provider=selected_provider)
                    elapsed = time.time() - start_time

                st.markdown("### 💡 Answer")
                st.info(answer)
                st.caption(f"⏱️ Generated in {elapsed:.2f}s using {selected_provider.upper()}")

        with tab4:
            st.subheader("🔬 Compare AI Providers")
            st.markdown("Compare how different AI models analyze the same article.")

            if len(available_providers) < 2:
                st.info("⚠️ Need at least 2 AI providers configured to use comparison feature.")
                st.markdown("Configure additional providers in your `.env` file:")
                st.code("""
ANTHROPIC_API_KEY=your_key_here
KIMI_API_KEY=your_key_here
QWEN_API_KEY=your_key_here
                """)
            else:
                article_idx = st.selectbox(
                    "Select Article to Compare",
                    range(len(articles)),
                    format_func=lambda x: f"Article {x + 1}: {articles[x]['title'][:60]}..."
                )

                comparison_task = st.radio(
                    "Comparison Task",
                    ["Summarize", "Extract Key Points"],
                    horizontal=True
                )

                if st.button("🔄 Compare All Providers", type="primary"):
                    article = articles[article_idx]

                    st.markdown(f"**Article:** {article['title']}")
                    st.divider()

                    task_type = "summarize" if comparison_task == "Summarize" else "extract_key_points"

                    with st.spinner("Generating responses from all providers..."):
                        results = analyzer.compare_ai_responses(
                            article,
                            task=task_type,
                            style="concise"
                        )

                    for provider, response in results.items():
                        with st.expander(f"🤖 {provider.upper()}", expanded=True):
                            st.markdown(response)

    else:
        # Welcome message
        st.info("👈 Enter a search query in the sidebar to get started!")

        # Show available providers
        st.subheader("🤖 Available AI Providers")
        cols = st.columns(len(available_providers))
        for idx, provider in enumerate(available_providers):
            with cols[idx]:
                info = analyzer.get_provider_info(provider)
                st.markdown(f"""
                **{info.get('name', provider)}**
                - Provider: {info.get('provider', 'N/A')}
                - Model: {info.get('model', 'N/A')}
                """)

        # Examples
        st.subheader("📝 Example Searches")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            - `diabetes machine learning`
            - `COVID-19 treatment`
            - `alzheimer disease biomarkers`
            """)

        with col2:
            st.markdown("""
            - `cancer immunotherapy[Title]`
            - `hypertension AND diet`
            - `CRISPR gene editing`
            """)

        st.subheader("✨ Features")
        st.markdown("""
        - 🔍 **PubMed Search**: Access millions of biomedical articles
        - 🤖 **Multi-AI Support**: Choose between Claude, Kimi, or Qwen
        - 📊 **Synthesis**: Combine insights from multiple papers
        - 💬 **Q&A**: Ask questions about the literature
        - 🔬 **AI Comparison**: Compare responses from different AI models
        """)

    # Footer
    st.divider()
    st.caption("⚠️ This tool is for research purposes only. Always verify medical information with healthcare professionals.")


if __name__ == "__main__":
    main()
