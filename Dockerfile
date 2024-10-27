FROM python:3.12-slim

# Установка переменных окружения
ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PATH "/app/scripts:${PATH}"
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование файлов проекта
COPY . .

# Создание необходимых директорий
RUN mkdir -p \
    /data/knowledge \
    /chroma/chroma \
    /var/lib/postgresql/data \
    /data/redis

# Установка прав на выполнение скриптов
RUN if [ -d "scripts" ]; then chmod +x scripts/*; fi

# Применение миграций при запуске
RUN echo '#!/bin/sh' > /entrypoint.sh \
    && echo 'alembic upgrade head' >> /entrypoint.sh \
    && echo 'python -m bot' >> /entrypoint.sh \
    && chmod +x /entrypoint.sh

# Открытие портов
EXPOSE 8080

# Запуск бота
ENTRYPOINT ["/entrypoint.sh"]

