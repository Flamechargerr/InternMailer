FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium)
RUN python -m playwright install --with-deps chromium

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data campaign_results backups cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=web.web_dashboard
ENV FLASK_DEBUG=0

# Expose port
EXPOSE 5050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from middleware.health_check import get_health_checker; hc = get_health_checker(); exit(0 if hc.run_all_checks()['status'] == 'pass' else 1)"

# Run application
CMD ["python", "main.py"]
