# Hosted demo image (T7). Synthetic data only. Secrets come from the platform's environment
# (NEBIUS_API_KEY, TAVILY_API_KEY), never from the image: .env is excluded by .dockerignore.
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt
COPY . .
# Public demo: each browser session gets its own seeded database and a model-call budget.
ENV DDP_DEMO_MODE=1 \
    DDP_DEMO_MAX_MODEL_CALLS=40
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
