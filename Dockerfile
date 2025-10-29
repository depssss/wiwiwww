FROM python:3.11-slim

WORKDIR /app

# non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy code (assume src/)
COPY src/ ./src/

EXPOSE 8080

CMD ["python", "-m", "src.main"]
