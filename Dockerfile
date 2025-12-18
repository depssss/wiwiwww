# Base image python yang ringan
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Buat direktori kerja
WORKDIR /app

# Buat user non-root demi keamanan (Poin e)
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh folder source code
COPY src/ ./src/

# Ganti ke user non-root
USER appuser

# Expose port
EXPOSE 8080

# Command default (jalankan Aggregator)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]