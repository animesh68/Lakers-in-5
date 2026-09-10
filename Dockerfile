# ==============================================================================
# Lakers in 5 — Production Dockerfile
# Multi-purpose slim image for FastAPI inference service & Streamlit monitoring dashboard
# ==============================================================================

FROM python:3.11-slim as runtime

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

# Create runtime directory for predictions/monitoring if using fallback storage
RUN mkdir -p /app/data/monitoring && chown -R appuser:appgroup /app/data/monitoring

# Switch to non-root user
USER appuser

# Expose ports for FastAPI (8000) and Streamlit Dashboard (8501)
EXPOSE 8000 8501

# Healthcheck targeting the application's native /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command: Production FastAPI ASGI server
CMD ["uvicorn", "src.inference.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--timeout-keep-alive", "30"]
