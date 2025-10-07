FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    netcat-openbsd \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and README
COPY requirements.txt README.md ./

# Copy application code (needed for poetry install)
COPY src/ ./src/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Install dependencies
RUN pip install -r requirements.txt

# Copy remaining files
COPY docker-entrypoint.sh ./

# Debug: Verify files were copied correctly
RUN echo "Contents of /app:" && ls -la /app/ && \
    echo "Contents of /app/src:" && ls -la /app/src/ && \
    echo "Contents of /app/src/app:" && ls -la /app/src/app/ || true

# Create directories for data and logs
RUN mkdir -p /app/data /app/logs

# Make entrypoint executable and create non-root user
RUN chmod +x docker-entrypoint.sh && \
    useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint and default command
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
