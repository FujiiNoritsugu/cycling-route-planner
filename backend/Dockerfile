# Backend Dockerfile for Cloud Run
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy backend dependencies first for better caching
COPY backend/pyproject.toml backend/uv.lock ./backend/
RUN cd backend && uv sync --frozen --no-dev

# Copy application code
COPY backend/app ./backend/app
COPY planner ./planner

# Set PYTHONPATH to include planner module
ENV PYTHONPATH=/app:/app/backend:$PYTHONPATH

# Expose port (Cloud Run uses PORT environment variable)
ENV PORT=8080
EXPOSE 8080

# Run the application
CMD cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
