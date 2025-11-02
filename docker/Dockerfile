FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    curl libpq-dev gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

EXPOSE 8080
CMD ["uv", "run", "python", "api_runner.py"]