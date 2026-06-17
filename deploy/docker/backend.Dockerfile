FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2/asyncpg build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir .

# Source
COPY backend/src/ ./src/
COPY contracts/ ./contracts/

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
