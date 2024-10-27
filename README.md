Вот обновленный README.md с учетом текущих проблем и их решений:

# Silavik - Виртуальный ассистент для документации

[Предыдущее описание остается без изменений до раздела "Установка и запуск"]

## Установка и запуск

### Предварительные требования

1. Установите Docker и Docker Compose
2. Убедитесь, что порты 8080, 6379, 5432 и 8000 свободны
3. Установите LibreOffice для конвертации документов (для локальной разработки)

### Быстрый старт

1. Клонирование репозитория:
```bash
git clone https://github.com/Xpos587/pfd-aiogram-2024
cd pfd-aiogram-2024
```

2. Настройка переменных окружения:
```bash
cp .env.dist .env
```

3. Отредактируйте файл `.env`:
```env
# Основные настройки бота
BOT_TOKEN=<ваш токен от BotFather>
ADMIN_IDS=<id администраторов через запятую>
TIME_ZONE=Europe/Moscow

# Настройки сервера
SERVER_PORT=8080

# PostgreSQL
POSTGRES_HOST=postgres  # Используйте localhost для локальной разработки
POSTGRES_PORT=5432
POSTGRES_DB=default
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<ваш пароль>

# Redis
REDIS_HOST=redis  # Используйте localhost для локальной разработки
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<ваш пароль>

# ChromaDB
CHROMA_HOST=chroma  # Используйте localhost для локальной разработки
CHROMA_PORT=8000
CHROMA_COLLECTION=documents

# Обработка документов
KNOWLEDGE_DATA=/data/knowledge
EMBEDDING_MODEL=cointegrated/LaBSE-en-ru
```

4. Создайте необходимые директории:
```bash
mkdir -p data/knowledge chroma/chroma
```

5. Запуск сервисов:
```bash
docker compose up -d --build
```

### Проверка работоспособности

1. Проверьте статус контейнеров:
```bash
docker compose ps
```

2. Проверьте логи:
```bash
docker compose logs -f
```

### Устранение проблем

1. Если возникает ошибка подключения к Redis:
```bash
# Проверьте настройки в .env
REDIS_HOST=redis  # Для Docker
REDIS_HOST=localhost  # Для локальной разработки
```

2. Если возникает ошибка "handle_some_error() missing i18n":
```bash
# Убедитесь, что папка locales существует и содержит файлы локализации
mkdir -p locales/ru locales/en
```

3. Если возникают проблемы с правами доступа:
```bash
# Установите правильные права на папки данных
sudo chown -R 1000:1000 data chroma
```

## Локальная разработка

[Предыдущие инструкции по локальной разработке остаются без изменений]

## Структура проекта

```
├── bot/                    # Telegram бот
├── services/              # Бизнес-логика
├── src/                   # Обработчик документов
│   ├── document_converter.py   # Конвертация документов
│   └── knowledge_base_watcher.py # Отслеживание изменений
├── migrations/            # Миграции базы данных
├── locales/              # Файлы локализации
└── docker/               # Docker конфигурация
```

[Остальные разделы остаются без изменений]

## Разработка и тестирование

1. Запуск тестов:
```bash
make test
```

2. Проверка форматирования:
```bash
make lint
```

3. Обновление переводов:
```bash
make i18n
```

4. Создание миграции:
```bash
make migration message="Описание изменений"
```

## Мониторинг и логи

- Логи бота: `docker compose logs -f bot`
- Логи обработчика документов: `docker compose logs -f document-processor`
- Логи ChromaDB: `docker compose logs -f chroma`

[Остальные разделы остаются без изменений]
