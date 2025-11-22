# Mooltiproxy Dockerfile
# Multi-stage build for minimal image size

# Stage 1: Base image with dependencies
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies (if needed in future)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies installation
FROM base as dependencies

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Final production image
FROM base as production

# Copy installed dependencies from previous stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash mooltiproxy && \
    chown -R mooltiproxy:mooltiproxy /app

# Copy application code
COPY --chown=mooltiproxy:mooltiproxy *.py ./
COPY --chown=mooltiproxy:mooltiproxy config_template.yaml ./

# Create directories for certificates and config
RUN mkdir -p certificates && \
    chown -R mooltiproxy:mooltiproxy certificates

# Switch to non-root user
USER mooltiproxy

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MOOLTIPROXY_KEY=""

# Expose port (default 8000)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Default command
CMD ["python", "-m", "main"]
