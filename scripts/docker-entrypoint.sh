#!/bin/bash
set -e

# Применение миграций базы данных
echo "Applying database migrations..."
alembic upgrade head

# Запуск обработчика документов в фоновом режиме
echo "Starting document processor..."
python -m src &

# Запуск бота
echo "Starting bot..."
exec python -m bot

