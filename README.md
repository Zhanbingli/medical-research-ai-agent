# 📚 Medical Literature Agent - Multi-AI Edition

An advanced AI-powered tool for searching, analyzing, and synthesizing medical literature from PubMed. Built with Python and Streamlit, supporting **multiple AI providers**: Claude (Anthropic), Kimi (月之暗面), and Qwen (通义千问).

## ✨ Features

- 🔍 **PubMed Search**: Access millions of biomedical research articles
- 🤖 **Multi-AI Support**: Choose between Claude, Kimi, or Qwen for analysis
- 📊 **Multi-Article Synthesis**: Combine insights from multiple papers
- 💬 **Q&A System**: Ask questions and get AI-powered answers with citations
- 🔬 **AI Comparison**: Compare how different AI models analyze the same article
- 📅 **Advanced Filtering**: Filter by date range, sort by relevance or date
- ⏱️ **Performance Tracking**: Monitor response times for each AI provider
- 🎯 **Medical Focus**: Specialized for biomedical and clinical research

## 🚀 Quick Start

### Prerequisites

- Docker (or Docker Desktop) with BuildKit enabled
- 至少配置一个 AI 提供商 API Key（填入 `.env`）

### Run (Docker only, ultra-simple)

```bash
# 1) 准备环境变量
.env
# 填写 ANTHROPIC_API_KEY / KIMI_API_KEY / QWEN_API_KEY / PUBMED_EMAIL 等

# 2) 一键启动
docker-compose up --build

# 若不使用 compose：
# docker build -t med-paper .
# docker run --env-file .env -p 8501:8501 med-paper
```

### Configuration

Edit `.env` file with your API keys:

```bash
# AI Provider API Keys (configure at least one)
ANTHROPIC_API_KEY=sk-ant-xxxxx           # Claude
KIMI_API_KEY=sk-xxxxx                    # Kimi/月之暗面
QWEN_API_KEY=sk-xxxxx                    # 通义千问

# Default provider: claude, kimi, or qwen
DEFAULT_AI_PROVIDER=claude

# PubMed configuration
PUBMED_EMAIL=your_email@example.com      # Recommended for better rate limits
```

## 📖 Usage Guide

### 1. Select AI Provider

In the sidebar, choose your preferred AI model:
- **Claude (Anthropic)**: High-quality analysis, excellent for complex synthesis
- **Kimi (月之暗面)**: Strong Chinese language support, fast responses
- **Qwen (通义千问)**: Alibaba's model, good for multilingual content

### 2. Search PubMed

1. Enter a search query (e.g., "diabetes machine learning")
2. Adjust number of results (1-20)
3. Choose sort order (relevance or publication date)
4. Optionally filter by date range
5. Click "Search"

### 3. Analyze Results

**📑 Articles Tab:**
- View article details (title, authors, abstract, keywords)
- Click "AI Summary" for concise summaries
- Click "Key Points" for structured extraction

**📊 Synthesis Tab:**
- Generate comprehensive analysis of all articles
- Optionally provide a specific research question
- Get synthesized findings, themes, and implications

**💬 Q&A Tab:**
- Ask specific questions about the literature
- Get answers with citations to source articles

**🔬 AI Comparison Tab:**
- Compare responses from all configured AI providers
- Analyze differences in interpretation and style
- Requires at least 2 AI providers configured

### Advanced Search Examples

```
diabetes machine learning          # Basic keyword search
COVID-19 treatment[Title]          # Search in title only
hypertension AND diet              # Boolean AND
(cancer OR tumor) therapy          # Boolean OR
alzheimer disease biomarkers       # Multiple terms
"machine learning"[MeSH]          # MeSH term search
```

## 🏗️ Project Structure

```
med_paper/
├── app.py                         # Main Streamlit application (Multi-AI)
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
├── setup.sh                       # Automated setup script
├── test_setup.py                  # Installation test script
├── src/
│   ├── __init__.py
│   ├── agents/                    # AI analysis modules
│   │   ├── __init__.py
│   │   ├── analyzer.py            # Original Claude analyzer
│   │   └── multi_ai_analyzer.py   # Multi-AI analyzer
│   ├── data_sources/              # Data retrieval
│   │   ├── __init__.py
│   │   └── pubmed_client.py       # PubMed API client
│   └── utils/                     # Utilities
│       ├── __init__.py
│       └── ai_client.py           # Unified AI client manager
├── data/                          # Local data (gitignored)
├── cache/                         # Cache directory (gitignored)
└── tests/                         # Unit tests
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Optional* | Claude API key from Anthropic |
| `KIMI_API_KEY` | Optional* | Kimi API key from Moonshot AI |
| `QWEN_API_KEY` | Optional* | Qwen API key from Alibaba Cloud |
| `DEFAULT_AI_PROVIDER` | No | Default AI (claude/kimi/qwen) |
| `PUBMED_EMAIL` | No | Email for PubMed API (recommended) |
| `CACHE_DIR` | No | Cache directory (default: ./cache) |
| `CACHE_EXPIRY_DAYS` | No | Cache expiration in days (default: 7) |

*At least one AI provider API key is required.

### AI Provider Comparison

| Provider | Strengths | Best For |
|----------|-----------|----------|
| **Claude** | High-quality reasoning, detailed analysis | Complex synthesis, research questions |
| **Kimi** | Fast responses, Chinese support | Quick summaries, bilingual content |
| **Qwen** | Multilingual, cost-effective | Large-scale processing, Chinese medical terms |

## 📚 API Usage

### Using Multi-AI Analyzer Programmatically

```python
from src.data_sources import PubMedClient
from src.agents import MultiAIAnalyzer

# Initialize
pubmed = PubMedClient(email="your@email.com")
analyzer = MultiAIAnalyzer(default_provider="claude")

# Search PubMed
articles = pubmed.search_and_fetch("diabetes treatment", max_results=5)

# Analyze with specific provider
summary = analyzer.summarize_article(articles[0], provider="kimi")

# Synthesize multiple articles
synthesis = analyzer.synthesize_multiple(articles, provider="qwen")

# Compare all providers
comparison = analyzer.compare_ai_responses(articles[0], task="summarize")
for provider, response in comparison.items():
    print(f"{provider}: {response}")
```

### Using Individual AI Clients

```python
from src.utils import AIClientManager

manager = AIClientManager()

# Get available providers
providers = manager.get_available_providers()
print(f"Available: {providers}")

# Generate with specific provider
response = manager.generate(
    prompt="Summarize this abstract...",
    provider="claude",
    max_tokens=500
)
```

## 🛠️ Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Test specific module
pytest tests/test_ai_client.py

# Test with coverage
pytest --cov=src tests/
```

### Adding New AI Providers

1. Create a new client class in `src/utils/ai_client.py`:

```python
class NewAIClient(BaseAIClient):
    def __init__(self, api_key: str):
        # Initialize API client
        pass

    def generate(self, prompt, ...):
        # Implement generation
        pass

    def get_model_info(self):
        # Return provider info
        pass
```

2. Register in `AIClientManager.SUPPORTED_PROVIDERS`

3. Add environment variable to `.env.example`

4. Update documentation

### Extending Analysis Capabilities

Modify `src/agents/multi_ai_analyzer.py`:

```python
def new_analysis_method(self, article, provider=None):
    prompt = f"Your custom prompt for {article['title']}"
    return self.ai_manager.generate(
        prompt=prompt,
        provider=provider or self.default_provider
    )
```

## 📋 Roadmap

### Completed ✅
- [x] Multi-AI provider support (Claude, Kimi, Qwen)
- [x] AI comparison feature
- [x] Performance tracking
- [x] Unified AI client manager

### Planned 🚧
- [ ] Vector database integration (Chroma/Pinecone)
- [ ] RAG-based semantic search
- [ ] PDF full-text download and analysis
- [ ] Citation network visualization
- [ ] Export to BibTeX/EndNote/Zotero
- [ ] Batch processing for systematic reviews
- [ ] Medical entity recognition (NER)
- [ ] Knowledge graph construction
- [ ] Multi-language interface
- [ ] API rate limiting and quota management
- [ ] Cost tracking per AI provider

## 🎯 Use Cases

### 1. Literature Review
- Search for relevant papers on your research topic
- Generate AI summaries to quickly assess relevance
- Synthesize findings across multiple studies

### 2. Research Question Exploration
- Ask specific questions about a body of literature
- Compare how different AI models interpret the evidence
- Identify research gaps and contradictions

### 3. Clinical Information Gathering
- Search for latest treatment guidelines
- Extract key clinical implications
- Compare perspectives from different AI models

### 4. Medical Education
- Learn about medical topics through AI-powered summaries
- Understand complex papers with detailed breakdowns
- Compare different AI explanation styles

## ⚠️ Limitations

- **Research Tool Only**: For research and educational purposes. Always verify with healthcare professionals
- **API Limits**: Each provider has rate limits and quotas
- **Abstract-Based**: Currently analyzes abstracts; full-text support coming soon
- **AI Accuracy**: AI summaries should be verified against original sources
- **Language**: Best performance in English; varies by provider for other languages
- **Cost**: API calls cost money; monitor your usage
- **Network Required**: Requires internet for PubMed and AI APIs

## 💡 Tips for Best Results

1. **Choose the Right AI**:
   - Use Claude for complex analysis
   - Use Kimi for Chinese content
   - Use Qwen for cost-effective processing

2. **Refine Your Queries**:
   - Use PubMed advanced syntax
   - Specify date ranges for recent research
   - Use MeSH terms for precise results

3. **Compare AI Responses**:
   - Use comparison feature for critical analysis
   - Different models may highlight different aspects

4. **Verify Information**:
   - Always check original sources
   - Cross-reference with multiple articles
   - Consult healthcare professionals for clinical decisions

## 🤝 Contributing

Contributions are welcome! Areas of interest:

- Adding new AI providers
- Improving analysis prompts
- Adding data sources (Semantic Scholar, arXiv)
- Enhancing UI/UX
- Writing tests
- Documentation improvements

## 📄 License

MIT License - free to use for research and educational purposes.

## 🙏 Acknowledgments

- **PubMed/NCBI**: Free access to biomedical literature
- **Anthropic**: Claude AI API
- **Moonshot AI**: Kimi API
- **Alibaba Cloud**: Qwen/通义千问 API
- **Biopython**: E-utilities Python interface
- **Streamlit**: Web application framework

## 📞 Support

### Getting Help

- Check this README for basic usage
- Run `python test_setup.py` to diagnose issues
- Review `.env.example` for configuration

### API Documentation

- **Claude**: https://docs.anthropic.com/
- **Kimi**: https://platform.moonshot.cn/docs
- **Qwen**: https://help.aliyun.com/zh/dashscope/
- **PubMed**: https://www.ncbi.nlm.nih.gov/books/NBK25501/

### Troubleshooting

**No AI providers available:**
- Check API keys in `.env`
- Verify keys are valid
- Check internet connection

**PubMed search fails:**
- Check search syntax
- Try simpler queries
- Verify internet connection
- Add email to `PUBMED_EMAIL`

**Slow responses:**
- Choose faster AI provider (Kimi is usually fastest)
- Reduce number of articles
- Check your internet speed

---

**Disclaimer**: This tool is for research and educational purposes only. It should not be used for clinical decision-making without proper verification by qualified healthcare professionals.

**Version**: 0.2.0 (Multi-AI Edition)
**Last Updated**: 2025-10-09
