"""
Enhanced multi-AI literature analyzer supporting Claude, Kimi, and Qwen.
"""
from typing import List, Dict, Optional
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils import AIClientManager


class MultiAIAnalyzer:
    """Analyze medical literature using multiple AI providers."""

    def __init__(self, default_provider: Optional[str] = None):
        """
        Initialize analyzer with AI client manager.

        Args:
            default_provider: Default AI provider (claude, kimi, qwen)
        """
        self.ai_manager = AIClientManager()
        self.default_provider = default_provider or os.getenv("DEFAULT_AI_PROVIDER", "claude")

        # Check if default provider is available
        available = self.ai_manager.get_available_providers()
        if not available:
            raise ValueError(
                "No AI providers configured. Please set API keys in .env file."
            )

        if self.default_provider not in available:
            print(f"Warning: {self.default_provider} not available. Using {available[0]}")
            self.default_provider = available[0]

    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers."""
        return self.ai_manager.get_available_providers()

    def get_provider_info(self, provider: Optional[str] = None) -> Dict:
        """Get information about an AI provider."""
        return self.ai_manager.get_provider_info(provider or self.default_provider)

    def summarize_article(
        self,
        article: Dict,
        style: str = "concise",
        provider: Optional[str] = None
    ) -> str:
        """
        Generate a summary of a single article.

        Args:
            article: Article dictionary from PubMed
            style: Summary style ('concise', 'detailed', 'clinical')
            provider: AI provider to use (None for default)

        Returns:
            Summary text
        """
        title = article.get("title", "")
        abstract = article.get("abstract", "")
        authors = ", ".join(article.get("authors", [])[:5])
        journal = article.get("journal", "")
        year = article.get("pub_date", "").split()[0] if article.get("pub_date") else ""

        if not abstract:
            return f"No abstract available for: {title}"

        prompt = self._build_summary_prompt(
            title, abstract, authors, journal, year, style
        )

        return self.ai_manager.generate(
            prompt=prompt,
            provider=provider or self.default_provider,
            max_tokens=1024,
            temperature=0.7
        )

    def synthesize_multiple(
        self,
        articles: List[Dict],
        research_question: Optional[str] = None,
        provider: Optional[str] = None
    ) -> str:
        """
        Synthesize findings from multiple articles.

        Args:
            articles: List of article dictionaries
            research_question: Optional specific question to address
            provider: AI provider to use

        Returns:
            Synthesis text
        """
        if not articles:
            return "No articles provided for synthesis."

        # Prepare article summaries
        article_texts = []
        for i, article in enumerate(articles, 1):
            title = article.get("title", "")
            abstract = article.get("abstract", "")
            year = article.get("pub_date", "").split()[0] if article.get("pub_date") else ""

            article_texts.append(
                f"Article {i}:\n"
                f"Title: {title}\n"
                f"Year: {year}\n"
                f"Abstract: {abstract}\n"
            )

        combined_text = "\n\n".join(article_texts)

        prompt = f"""You are a medical research expert. Analyze the following {len(articles)} research articles and provide a comprehensive synthesis.

{combined_text}

Please provide:
1. **Key Findings**: Main conclusions across all studies
2. **Common Themes**: Recurring topics and methodologies
3. **Contradictions**: Any conflicting results or interpretations
4. **Research Gaps**: What remains unclear or needs further study
5. **Clinical Implications**: Practical applications if applicable

{"Focus specifically on: " + research_question if research_question else ""}

Provide a well-structured synthesis in markdown format."""

        return self.ai_manager.generate(
            prompt=prompt,
            provider=provider or self.default_provider,
            max_tokens=2048,
            temperature=0.7
        )

    def extract_key_points(
        self,
        article: Dict,
        provider: Optional[str] = None
    ) -> str:
        """
        Extract structured key points from an article.

        Args:
            article: Article dictionary
            provider: AI provider to use

        Returns:
            Extracted key points as text
        """
        abstract = article.get("abstract", "")
        if not abstract:
            return "No abstract available"

        prompt = f"""Analyze this medical research abstract and extract key information:

Title: {article.get('title', '')}
Abstract: {abstract}

Extract and return:
1. Main objective/research question
2. Methods used
3. Key findings (3-5 bullet points)
4. Main conclusion
5. Clinical significance (if applicable)

Format as a structured list."""

        return self.ai_manager.generate(
            prompt=prompt,
            provider=provider or self.default_provider,
            max_tokens=800,
            temperature=0.7
        )

    def answer_question(
        self,
        articles: List[Dict],
        question: str,
        provider: Optional[str] = None
    ) -> str:
        """
        Answer a specific question based on provided articles.

        Args:
            articles: List of article dictionaries
            question: Question to answer
            provider: AI provider to use

        Returns:
            Answer text with citations
        """
        if not articles:
            return "No articles provided to answer the question."

        # Build context from articles
        context = []
        for i, article in enumerate(articles, 1):
            context.append(
                f"[{i}] {article.get('title', '')}\n"
                f"Abstract: {article.get('abstract', '')}\n"
                f"PMID: {article.get('pmid', '')}"
            )

        context_text = "\n\n".join(context)

        prompt = f"""You are a medical research assistant. Based on the following research articles, answer this question:

Question: {question}

Available Research:
{context_text}

Provide a comprehensive answer that:
1. Directly addresses the question
2. Cites specific studies using [number] notation
3. Notes any limitations or conflicting evidence
4. Indicates if the available research is insufficient to fully answer

Answer:"""

        return self.ai_manager.generate(
            prompt=prompt,
            provider=provider or self.default_provider,
            max_tokens=1500,
            temperature=0.7
        )

    def compare_ai_responses(
        self,
        article: Dict,
        task: str = "summarize",
        style: str = "concise"
    ) -> Dict[str, str]:
        """
        Compare responses from all available AI providers.

        Args:
            article: Article dictionary
            task: Task type ('summarize', 'extract_key_points')
            style: Summary style for summarization

        Returns:
            Dictionary mapping provider names to responses
        """
        results = {}
        providers = self.get_available_providers()

        for provider in providers:
            if task == "summarize":
                results[provider] = self.summarize_article(
                    article, style=style, provider=provider
                )
            elif task == "extract_key_points":
                results[provider] = self.extract_key_points(
                    article, provider=provider
                )

        return results

    def _build_summary_prompt(
        self,
        title: str,
        abstract: str,
        authors: str,
        journal: str,
        year: str,
        style: str
    ) -> str:
        """Build prompt for article summarization."""
        style_instructions = {
            "concise": "Provide a concise 3-4 sentence summary focusing on the main finding and its significance.",
            "detailed": "Provide a detailed summary covering background, methods, results, and conclusions.",
            "clinical": "Focus on clinical implications and practical applications for healthcare providers."
        }

        instruction = style_instructions.get(style, style_instructions["concise"])

        return f"""Summarize this medical research article:

Title: {title}
Authors: {authors}
Journal: {journal} ({year})

Abstract:
{abstract}

{instruction}

Summary:"""


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    from src.data_sources import PubMedClient

    load_dotenv()

    try:
        analyzer = MultiAIAnalyzer()
        pubmed = PubMedClient()

        print(f"Available AI providers: {analyzer.get_available_providers()}")
        print(f"Using default: {analyzer.default_provider}")

        # Get an article
        articles = pubmed.search_and_fetch("diabetes", max_results=1)

        if articles:
            article = articles[0]
            print(f"\nTitle: {article['title']}\n")

            # Compare all AI providers
            print("Comparing AI responses...\n")
            results = analyzer.compare_ai_responses(article, task="summarize")

            for provider, response in results.items():
                print(f"{'='*50}")
                print(f"{provider.upper()}")
                print(f"{'='*50}")
                print(response)
                print()

    except Exception as e:
        print(f"Error: {e}")
