# Use specific Python version for stability
FROM python:3.10.12-slim

# Add build metadata
LABEL maintainer="Sniff AI Team" \
      version="1.0" \
      description="ML Model Service"

# Set working directory
WORKDIR /app

# Copy requirements from repo root
COPY ../requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy model files
COPY . .

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the entry point
CMD ["python", "main.py"]