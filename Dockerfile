FROM python:3.10-slim

WORKDIR /workspace

# Install system git client (required by GitPython for repo loading)
# and curl (used by the container HEALTHCHECK below).
RUN apt-get update && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run as a non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /workspace/data \
    && chown -R appuser:appuser /workspace
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# WEB_CONCURRENCY controls the number of gunicorn/uvicorn workers in production.
# PORT is provided automatically by hosts like Render; defaults to 8000 otherwise
# (e.g. plain `docker compose up`, where we still publish container port 8000).
ENV WEB_CONCURRENCY=2
ENV PORT=8000

CMD ["sh", "-c", "gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT} -w ${WEB_CONCURRENCY} --timeout 120"]
