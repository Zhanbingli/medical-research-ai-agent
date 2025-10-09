"""
Advanced Medical Literature Agent with:
- Intelligent caching
- Cost tracking
- Error retry with fallback
- Autonomous agent mode
- Performance monitoring
"""
import streamlit as st
import os
from dotenv import load_dotenv
import sys
from pathlib import Path
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_sources import PubMedClient
from src.agents import MultiAIAnalyzer
from src.agents.medical_agent import MedicalResearchAgent
from src.utils import get_cache_manager, get_cost_tracker

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Medical Literature Agent - Advanced",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize managers
cache_manager = get_cache_manager()
cost_tracker = get_cost_tracker()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4 0%, #ff7f0e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .cost-display {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2ca02c;
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


def initialize_clients():
    """Initialize clients."""
    try:
        pubmed = PubMedClient(email=os.getenv("PUBMED_EMAIL"))
        analyzer = MultiAIAnalyzer()
        agent = MedicalResearchAgent()
        return pubmed, analyzer, agent
    except Exception as e:
        st.error(f"Initialization Error: {e}")
        return None, None, None


def display_cost_metrics():
    """Display cost and usage metrics."""
    stats = cost_tracker.get_usage_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Cost",
            value=f"${stats['total_cost']:.4f}",
            delta=None
        )

    with col2:
        st.metric(
            label="Total Tokens",
            value=f"{stats['total_tokens']:,}",
            delta=None
        )

    with col3:
        st.metric(
            label="API Calls",
            value=stats['total_requests'],
            delta=None
        )

    with col4:
        cache_stats = cache_manager.get_cache_stats()
        st.metric(
            label="Cached Items",
            value=cache_stats['ai_cache']['size'] + cache_stats['pubmed_cache']['size'],
            delta=None
        )


def display_cache_management():
    """Display cache management controls."""
    st.subheader("🗄️ Cache Management")

    cache_stats = cache_manager.get_cache_stats()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**AI Response Cache**")
        st.write(f"Items: {cache_stats['ai_cache']['size']}")
        st.write(f"Size: {cache_stats['ai_cache']['bytes'] / 1024:.2f} KB")

    with col2:
        st.markdown("**PubMed Query Cache**")
        st.write(f"Items: {cache_stats['pubmed_cache']['size']}")
        st.write(f"Size: {cache_stats['pubmed_cache']['bytes'] / 1024:.2f} KB")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Clear AI Cache"):
            cache_manager.clear_cache("ai")
            st.success("AI cache cleared!")
            st.rerun()

    with col2:
        if st.button("Clear PubMed Cache"):
            cache_manager.clear_cache("pubmed")
            st.success("PubMed cache cleared!")
            st.rerun()

    with col3:
        if st.button("Clear All Cache"):
            cache_manager.clear_cache("all")
            st.success("All cache cleared!")
            st.rerun()


def main():
    """Main application."""
    # Header
    st.markdown('<p class="main-header">🤖 Advanced Medical Literature Agent</p>', unsafe_allow_html=True)
    st.markdown("**Enterprise-grade AI Agent** with caching, cost tracking, and autonomous reasoning")

    # Initialize clients
    pubmed, analyzer, agent = initialize_clients()

    if not pubmed or not analyzer:
        st.stop()

    # Get available providers
    available_providers = analyzer.get_available_providers()

    if not available_providers:
        st.error("No AI providers available. Configure API keys in .env")
        st.stop()

    # Display metrics in main area
    with st.expander("📊 System Metrics", expanded=False):
        display_cost_metrics()

        st.divider()

        # Cost breakdown by provider
        stats = cost_tracker.get_usage_stats()

        if stats['by_provider']:
            st.subheader("Cost by Provider")
            for provider, data in stats['by_provider'].items():
                st.write(f"**{provider.upper()}**: ${data['cost']:.4f} ({data['requests']} requests)")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Mode selection
        mode = st.radio(
            "🎯 Operation Mode",
            ["Standard", "Autonomous Agent"],
            help="Standard: Direct queries. Agent: Multi-step reasoning with tools."
        )

        st.divider()

        # AI Provider
        st.subheader("🤖 AI Provider")

        provider_labels = {
            "claude": "Claude (Anthropic)",
            "kimi": "Kimi (月之暗面)",
            "qwen": "Qwen (通义千问)"
        }

        display_providers = [provider_labels.get(p, p) for p in available_providers]
        selected_display = st.selectbox("Select AI Model", display_providers)
        selected_provider = available_providers[display_providers.index(selected_display)]

        st.divider()

        # Cache settings
        st.subheader("🗄️ Cache Settings")
        use_cache = st.checkbox("Enable Caching", value=True)

        if use_cache:
            st.info("✓ Caching enabled - faster responses & lower costs")

        st.divider()

        # Cost limits
        st.subheader("💰 Cost Limits")
        daily_limit = st.number_input("Daily Limit ($)", min_value=0.0, value=10.0, step=1.0)
        monthly_limit = st.number_input("Monthly Limit ($)", min_value=0.0, value=100.0, step=10.0)

        quota = cost_tracker.check_quota(daily_limit, monthly_limit)

        if not quota['daily_within_limit']:
            st.error(f"⚠️ Daily limit exceeded!")

        if not quota['monthly_within_limit']:
            st.error(f"⚠️ Monthly limit exceeded!")

        st.write(f"Daily: ${quota['daily_used']:.2f} / ${daily_limit:.2f}")
        st.write(f"Monthly: ${quota['monthly_used']:.2f} / ${monthly_limit:.2f}")

        st.divider()

        # Search settings
        st.subheader("🔍 Search Settings")
        search_query = st.text_input("Search Query", placeholder="e.g., diabetes treatment")
        max_results = st.slider("Results", 1, 20, 5)
        sort_order = st.selectbox("Sort By", ["relevance", "pub_date"])

        search_button = st.button("🔍 Search", type="primary", use_container_width=True)

    # Main content
    if mode == "Autonomous Agent":
        st.subheader("🤖 Autonomous Agent Mode")
        st.markdown("""
        Ask complex questions and let the agent:
        - Search PubMed autonomously
        - Analyze multiple articles
        - Make multi-step plans
        - Provide comprehensive answers
        """)

        user_query = st.text_area(
            "Your Research Question",
            placeholder="e.g., What are the latest breakthrough treatments for Alzheimer's disease? Compare their effectiveness.",
            height=100
        )

        if st.button("🚀 Let Agent Work", type="primary"):
            if not user_query:
                st.warning("Please enter a question")
                st.stop()

            # Check quota
            if not quota['daily_within_limit'] or not quota['monthly_within_limit']:
                st.error("Cost limit exceeded. Please increase limits or wait.")
                st.stop()

            with st.spinner("🤖 Agent is thinking and working..."):
                agent_instance = MedicalResearchAgent(provider=selected_provider)

                # Stream agent progress
                progress_placeholder = st.empty()

                try:
                    answer = agent_instance.think(user_query, max_iterations=5)

                    st.success("✅ Agent completed the task!")
                    st.markdown("### 📝 Agent's Answer")
                    st.markdown(answer)

                    # Show conversation history
                    with st.expander("🔍 Agent's Reasoning Process"):
                        for msg in agent_instance.conversation_history:
                            st.markdown(f"**{msg['role'].upper()}**: {msg['content'][:300]}...")

                except Exception as e:
                    st.error(f"Agent error: {str(e)}")

    else:  # Standard mode
        if search_button:
            if not search_query:
                st.warning("Please enter a search query")
                st.stop()

            # Check quota
            if not quota['daily_within_limit'] or not quota['monthly_within_limit']:
                st.error("Cost limit exceeded. Please increase limits.")
                st.stop()

            # Check cache first
            cached_results = None
            if use_cache:
                cached_results = cache_manager.get_pubmed_query(
                    query=search_query,
                    max_results=max_results,
                    sort=sort_order
                )

            if cached_results:
                st.info("⚡ Results loaded from cache (instant & free!)")
                articles = cached_results
            else:
                with st.spinner(f"Searching PubMed for '{search_query}'..."):
                    articles = pubmed.search_and_fetch(
                        query=search_query,
                        max_results=max_results,
                        sort=sort_order
                    )

                # Cache results
                if use_cache and articles:
                    cache_manager.set_pubmed_query(
                        query=search_query,
                        max_results=max_results,
                        results=articles,
                        sort=sort_order
                    )

            if not articles:
                st.warning("No articles found")
                st.stop()

            st.session_state['articles'] = articles
            st.session_state['search_query'] = search_query

        # Display results
        if 'articles' in st.session_state:
            articles = st.session_state['articles']

            st.success(f"Found {len(articles)} articles")

            # Quick actions
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📊 Synthesize All Articles"):
                    with st.spinner("Synthesizing..."):
                        start_time = time.time()

                        synthesis = analyzer.synthesize_multiple(
                            articles, provider=selected_provider
                        )

                        elapsed = time.time() - start_time

                        # Estimate and record cost
                        tokens_estimate = len(synthesis.split()) * 2
                        cost = cost_tracker.record_usage(
                            provider=selected_provider,
                            model="default",
                            prompt_tokens=tokens_estimate,
                            completion_tokens=tokens_estimate,
                            operation="synthesize"
                        )

                        st.markdown(synthesis)
                        st.caption(f"⏱️ {elapsed:.2f}s | 💰 ${cost:.4f}")

            with col2:
                if st.button("🔬 Compare All Providers"):
                    if len(available_providers) < 2:
                        st.warning("Need 2+ providers for comparison")
                    else:
                        with st.spinner("Comparing providers..."):
                            results = analyzer.compare_ai_responses(
                                articles[0], task="summarize"
                            )

                            for prov, resp in results.items():
                                st.markdown(f"**{prov.upper()}**")
                                st.markdown(resp[:300] + "...")
                                st.divider()

            # Article list
            for idx, article in enumerate(articles):
                with st.expander(f"📄 Article {idx + 1}: {article['title'][:60]}..."):
                    st.markdown(f"**{article['title']}**")
                    st.caption(f"PMID: {article.get('pmid', 'N/A')}")
                    st.write(article.get('abstract', 'No abstract')[:500] + "...")

                    if st.button(f"🤖 AI Summary", key=f"sum_{idx}"):
                        with st.spinner("Generating summary..."):
                            summary = analyzer.summarize_article(
                                article, provider=selected_provider
                            )
                            st.info(summary)

    # Footer with cache management
    st.divider()

    with st.expander("🔧 Advanced Settings"):
        display_cache_management()

    st.caption("⚠️ For research purposes only. Verify information with healthcare professionals.")


if __name__ == "__main__":
    main()
