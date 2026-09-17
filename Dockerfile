# ==============================================================================
# Lakers in 5 — Production Multi-Stage Dockerfile
# Stage 1: Build React / Vite Frontend Dashboard
# Stage 2: Python 3.11 Runtime for Unified FastAPI & Static UI Serving
# ==============================================================================

# Stage 1: Build Frontend UI
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Production Runtime
FROM python:3.11-slim AS runtime

# Set environment variables for Python runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install runtime system packages (curl for container healthcheck, libgomp1 for ML runtimes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user and group
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash -m appuser

# Set application working directory
WORKDIR /app

# Install Python dependencies first for caching efficiency
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and runtime artifacts
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup scripts/ /app/scripts/
COPY --chown=appuser:appgroup models/ /app/models/
COPY --chown=appuser:appgroup data/processed/ /app/data/processed/
COPY --chown=appuser:appgroup data/features/ /app/data/features/
COPY --chown=appuser:appgroup configs/ /app/configs/

# Copy built frontend assets from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder --chown=appuser:appgroup /app/frontend/dist /app/frontend/dist

# Create runtime directory for logs and predictions/monitoring if using fallback storage
RUN mkdir -p /app/logs /app/data/monitoring && chown -R appuser:appgroup /app/logs /app/data/monitoring

# Switch to non-root user
USER appuser

# Expose ports for FastAPI (8000) and Streamlit Dashboard (8501)
EXPOSE 8000 8501

# Healthcheck targeting the application's native /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || python -c "import os, urllib.request; p = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{p}/health')" || exit 1

# Default command: Production FastAPI ASGI server dynamically binding to PORT with 1 worker for container memory safety
CMD ["sh", "-c", "uvicorn src.inference.api:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-1} --timeout-keep-alive 30"]

