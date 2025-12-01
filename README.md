# 📚 Medical Literature Agent - Multi-AI Edition

An AI assistant for searching, analyzing, and synthesizing medical literature from PubMed. Built with Python + Streamlit, supporting **multiple AI providers**: Claude, Kimi, and Qwen.

## ✨ Features

- 🔍 PubMed search: fetch recent biomedical papers and metadata
- 🤖 Multi-model analysis: Claude / Kimi / Qwen for summaries, key points, Q&A
- 📊 Multi-article synthesis: combined insights, commonalities, and differences
- 💬 Q&A with citations: answers grounded in retrieved articles
- 🔬 Model comparison: see how different models respond to the same paper

## 🚀 Quick Start (Docker)

1) Copy env template and add at least one API key  
`cp .env.example .env`

2) Start service  
`docker-compose up --build`

Open: http://localhost:8501

## 🔧 Minimal Config

In `.env`, set:
- `ANTHROPIC_API_KEY` or `KIMI_API_KEY` or `QWEN_API_KEY` (at least one)
- `DEFAULT_AI_PROVIDER` (claude/kimi/qwen, default claude)
- `PUBMED_EMAIL` (recommended for better NCBI rate limits)
