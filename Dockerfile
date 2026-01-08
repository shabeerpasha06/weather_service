# Use a slim Python image
FROM python:3.11-slim

# Keep Python from writing pyc files and buffer disabled
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install minimal build deps (some packages may need them)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd --create-home appuser

WORKDIR /app

# Copy and install dependencies first to leverage Docker caching
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Ensure app directory owned by non-root user
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Uvicorn entrypoint; single worker is fine for async apps in many cases
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio", "--log-level", "info"]
