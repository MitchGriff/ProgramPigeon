# --- Build stage ---
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies into a separate layer for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- Runtime stage ---
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from the builder stage (keeps the image lean)
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Run as a non-root user for security
RUN useradd --no-create-home appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
