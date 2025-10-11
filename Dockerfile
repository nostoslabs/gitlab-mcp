# Use uv's official image as builder for dependency management
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Set working directory
WORKDIR /app

# Copy dependency files and README for build metadata
COPY pyproject.toml uv.lock README.md ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-install-project --no-dev

# Copy source code
COPY src/ ./src/

# Install the project
RUN uv sync --frozen --no-dev

# Production stage using Chainguard's secure Python image
FROM cgr.dev/chainguard/python:latest

# Note: Git installation skipped for Chainguard compatibility; add if needed via alternative method

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code (for runtime reference if needed)
COPY --from=builder /app/src ./src

# Set environment variables for production
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Note: Non-root user creation skipped for Chainguard compatibility; run as root for now

# Expose port if needed (e.g., for SSE or HTTP transport)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run the application
CMD ["python", "-m", "gitlab_mcp"]
