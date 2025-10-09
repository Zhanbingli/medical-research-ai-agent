"""
AI-powered literature analysis using Claude.
Provides summarization, synthesis, and analysis capabilities.
"""
from typing import List, Dict, Optional
import anthropic
import os
from datetime import datetime


class LiteratureAnalyzer:
    """Analyze medical literature using Claude AI."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize analyzer with Claude API.

        Args:
            api_key: Anthropic API key (defaults to env variable)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def summarize_article(self, article: Dict, style: str = "concise") -> str:
        """
        Generate a summary of a single article.

        Args:
            article: Article dictionary from PubMed
            style: Summary style ('concise', 'detailed', 'clinical')

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

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def synthesize_multiple(
        self,
        articles: List[Dict],
        research_question: Optional[str] = None
    ) -> str:
        """
        Synthesize findings from multiple articles.

        Args:
            articles: List of article dictionaries
            research_question: Optional specific question to address

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

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            return f"Error generating synthesis: {str(e)}"

    def extract_key_points(self, article: Dict) -> Dict[str, List[str]]:
        """
        Extract structured key points from an article.

        Args:
            article: Article dictionary

        Returns:
            Dictionary with categorized key points
        """
        abstract = article.get("abstract", "")
        if not abstract:
            return {"error": ["No abstract available"]}

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

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            return {"key_points": response.content[0].text}

        except Exception as e:
            return {"error": [str(e)]}

    def answer_question(
        self,
        articles: List[Dict],
        question: str
    ) -> str:
        """
        Answer a specific question based on provided articles.

        Args:
            articles: List of article dictionaries
            question: Question to answer

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

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            return f"Error answering question: {str(e)}"

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
    # This requires ANTHROPIC_API_KEY in environment
    from src.data_sources import PubMedClient

    pubmed = PubMedClient()
    analyzer = LiteratureAnalyzer()

    # Get some articles
    articles = pubmed.search_and_fetch("diabetes treatment", max_results=3)

    if articles:
        # Summarize first article
        print("=== Article Summary ===")
        summary = analyzer.summarize_article(articles[0], style="concise")
        print(summary)

        # Synthesize multiple
        print("\n=== Synthesis of Multiple Articles ===")
        synthesis = analyzer.synthesize_multiple(articles)
        print(synthesis)
