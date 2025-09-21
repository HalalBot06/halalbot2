# HalalBot Production Dockerfile for Railway
# Optimized for fast deployment and CPU-only inference

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install CPU-only PyTorch first (this is the key!)
RUN pip install torch==2.2.2+cpu --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Create necessary directories
RUN mkdir -p data/history static

# Create non-root user for security
RUN useradd -m -u 1000 halalbot && chown -R halalbot:halalbot /app
USER halalbot

# Set environment variables for Railway
ENV PORT=8501

# Expose the port Railway expects
EXPOSE $PORT

# Health check for Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/_stcore/health || exit 1

# Run Streamlit with dynamic port from Railway
CMD streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.runOnSave=false \
    --server.fileWatcherType=none \
    --browser.gatherUsageStats=false
