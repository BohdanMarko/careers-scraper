FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BINARY=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY src/ src/

# Bake in config.example.yaml as config.yaml — contains vacancies/keywords but NO secrets.
# Telegram credentials are injected at runtime via TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env vars.
COPY config.example.yaml config.yaml

CMD ["python", "main.py"]
