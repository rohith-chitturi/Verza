FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy dependency files
COPY pyproject.toml uv.lock ./
COPY core/pyproject.toml core/
COPY interfaces/pyproject.toml interfaces/
COPY capabilities/pyproject.toml capabilities/

# Sync dependencies
RUN uv sync --no-dev

# Copy application code
COPY . .

# Run bootstrap/app
CMD ["python", "-m", "bootstrap.app"]
