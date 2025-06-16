FROM python:3.13-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install UV securely (uses HTTPS)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy requirements files
COPY pyproject.toml uv.lock ./

# Install dependencies
# Label to identify this layer for cache busting
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    uv pip install --system -e .

# Copy only the application source code and necessary files
COPY app/ ./app/
COPY alembic.ini ./
COPY migrations/ ./migrations/


# Create a non-root user and group
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Set ownership of the app directory
RUN chown -R appuser:appuser /app

# Explicitly set the default port for the service
# Render will override this with its own PORT environment variable
ENV PORT=8000

# Healthcheck uses the PORT environment variable
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f -X GET http://localhost:${PORT}/api/v1/health || exit 1

# Expose the default port
EXPOSE 8000

# Create entrypoint script to run migrations
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh && chown appuser:appuser /docker-entrypoint.sh

# Switch to non-root user
USER appuser

ENTRYPOINT ["/docker-entrypoint.sh"]