# Backend Dockerfile for Cloud Run
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY backend/pyproject.toml backend/uv.lock ./backend/
COPY planner/pyproject.toml planner/uv.lock ./planner/
COPY backend/app ./backend/app
COPY planner/planner ./planner/planner

# Set PYTHONPATH to include both backend and planner
ENV PYTHONPATH=/app:/app/backend:/app/planner:$PYTHONPATH

# Install dependencies for both backend and planner
RUN cd backend && uv sync --frozen --no-dev
RUN cd planner && uv sync --frozen --no-dev

# Expose port (Cloud Run uses PORT environment variable)
ENV PORT=8080
EXPOSE 8080

# Run the application
CMD cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
