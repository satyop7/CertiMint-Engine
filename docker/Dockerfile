FROM python:3.10-slim

WORKDIR /app

# Install system dependencies with better error handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    curl \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    gcc \
    g++ \
    build-essential \
    python3-dev \
    libc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome for web scraping phase (optional, as it won't be used in sandbox mode)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install ChromeDriver with better error handling
RUN set -ex && \
    CHROME_DRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    mkdir -p /tmp/chromedriver && \
    wget -q -O /tmp/chromedriver/chromedriver_linux64.zip chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver/chromedriver_linux64.zip -d /tmp/chromedriver && \
    mv /tmp/chromedriver/chromedriver /usr/bin/chromedriver && \
    chown root:root /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm -rf /tmp/chromedriver

# Create necessary directories
RUN mkdir -p /app/models /app/data

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies with better error handling
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py /app/
COPY run_workflow.sh /app/
COPY network_monitor.sh /app/

# Add placeholder for model
RUN touch /app/models/llama-3-8b-instruct.gguf

# Make scripts executable
RUN chmod +x /app/run_workflow.sh /app/network_monitor.sh

# Install network monitoring tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tcpdump \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Environment variables for sandbox mode
ENV PYTHONUNBUFFERED=1
ENV SANDBOX_MODE=true
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1
ENV LANGCHAIN_TRACING=false
ENV LLM_MODEL_PATH=/app/models/llama-3-8b-instruct.gguf

# Create an entrypoint script for more flexible operation
RUN echo '#!/bin/bash\n\
# Check if model exists and has content\n\
if [ ! -s "/app/models/llama-3-8b-instruct.gguf" ]; then\n\
    echo "LLM model missing or empty. Using mock LLM instead."\n\
fi\n\
\n\
# Check if we are in sandbox mode\n\
if [ "$SANDBOX_MODE" = "true" ]; then\n\
    echo "Running in sandbox mode with network isolation enabled."\n\
    echo "SECURITY NOTICE: This container should be run with: docker run --network=none"\n\
    \n\
    # Run with network monitoring in sandbox mode\n\
    if [ $# -gt 0 ]; then\n\
        exec /app/network_monitor.sh "$@"\n\
    else\n\
        exec /app/network_monitor.sh python main.py --file data/sample.pdf --subject "Computer Science" --id "DEFAULT"\n\
    fi\n\
else\n\
    # Non-sandbox mode (scraping phase)\n\
    if [ $# -gt 0 ]; then\n\
        exec "$@"\n\
    else\n\
        exec python main.py --file data/sample.pdf --subject "Computer Science" --id "DEFAULT"\n\
    fi\n\
fi' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

#EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
