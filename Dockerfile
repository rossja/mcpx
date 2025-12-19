# Build stage
FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
# Install dependencies into virtualenv
RUN uv sync --frozen --no-install-project

# Runtime stage
FROM python:3.13-slim-bookworm

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy app code
COPY app /app/app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Command
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}

