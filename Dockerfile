# ==========================================
# Build Stage
# ==========================================
FROM python:3.13-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# We use standard pip for dependency management in the container
# If using poetry/uv, this step would involve exporting to requirements.txt first
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install production dependencies
RUN pip install --no-cache-dir hatchling \
    && pip install --no-cache-dir .

# ==========================================
# Run Stage
# ==========================================
FROM python:3.13-slim AS runner

# Install runtime dependencies (PostgreSQL client libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd -m -s /bin/bash botuser

# Set working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

# Copy application source code
COPY src/ ./src/
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Create logs directory and set permissions
RUN mkdir -p /app/logs && chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Health check (pinging the health endpoint or a simple process check)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Command to run migrations and start the bot
CMD ["bash", "-c", "alembic upgrade head && python -m bot"]
