FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc libssl-dev libffi-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn gevent
RUN python -m playwright install --with-deps chromium

COPY src/ src/
COPY main.py pyproject.toml ./
COPY config/.env.example config/.env.production.example config/
COPY data/ data/
COPY assets/ assets/
COPY frontend/dist frontend/dist/ 2>/dev/null || true

RUN mkdir -p logs data/campaign_results backups cache

ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=web.web_dashboard
EXPOSE 5050

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from middleware.health_check import get_health_checker; hc = get_health_checker(); exit(0 if hc.run_all_checks()['status'] == 'pass' else 1)"

CMD ["python", "main.py"]
