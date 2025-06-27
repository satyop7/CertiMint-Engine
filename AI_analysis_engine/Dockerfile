FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1
ENV LANGCHAIN_TRACING=false
ENV SANDBOX_MODE=true

RUN mkdir -p data result models

CMD ["python3", "complete_workflow.py"]