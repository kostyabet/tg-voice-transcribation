FROM python:3.11-slim

# ffmpeg нужен Whisper для декодирования аудио.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

# Кэш скачанных моделей Whisper (монтируется как volume, чтобы не качать каждый раз).
ENV XDG_CACHE_HOME=/cache
VOLUME ["/cache"]

CMD ["python", "bot.py"]
