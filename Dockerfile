FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for Biopython and friends
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      curl \
      libxml2-dev \
      libxslt1-dev \
      zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Streamlit defaults for containerized, headless use
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHERUSAGESTATS=false \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_FILEWATCHER_TYPE=poll

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
