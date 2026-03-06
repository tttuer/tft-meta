FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml .

# Install dependencies (no venv, system install)
RUN uv pip install --system --no-cache -r pyproject.toml 2>/dev/null || \
    uv pip install --system --no-cache \
        fastapi==0.110.0 \
        "uvicorn[standard]==0.29.0" \
        sqlalchemy==2.0.29 \
        asyncpg==0.29.0 \
        alembic==1.13.1 \
        pydantic==2.6.4 \
        pydantic-settings==2.2.1 \
        redis==5.0.3 \
        httpx==0.27.0 \
        python-dotenv==1.0.1 \
        openai==1.14.3

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
