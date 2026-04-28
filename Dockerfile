FROM python:3.12-slim

WORKDIR /app

# Copy package metadata and source required by setuptools
COPY pyproject.toml README.md ./
COPY app/ app/

# Install backend dependencies and package
RUN pip install --no-cache-dir .

# Copy static game data
COPY data/ data/

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
