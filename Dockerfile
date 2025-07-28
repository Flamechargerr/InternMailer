# Dockerfile for InternMailer Failure Audit
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p resumes data templates src

# Install Ollama (for container testing)
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Expose ports
EXPOSE 8501 11434

# Create entrypoint script
RUN echo '#!/bin/bash\n\
# Start Ollama in background\n\
ollama serve &\n\
sleep 5\n\
# Pull Gemma3 model\n\
ollama pull gemma3:latest\n\
# Run audit tests\n\
python test_failures.py\n\
# Keep container running\n\
tail -f /dev/null' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
