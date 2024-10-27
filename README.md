# Silavik - Виртуальный ассистент для документации

Silavik - это Telegram-бот, созданный для помощи пользователям в работе с документацией программного обеспечения. Бот использует современные технологии обработки естественного языка для предоставления точных и контекстных ответов на вопросы пользователей.

## Особенности

- 🤖 Интеллектуальная обработка вопросов на естественном языке
- 📚 Поиск по документации с использованием векторной базы данных ChromaDB
- 💭 Контекстное понимание и генерация релевантных ответов
- 🔄 Система обратной связи для улучшения качества ответов
- 🌍 Поддержка русского языка
- 💾 Сохранение истории взаимодействий и обратной связи

## Технологический стек

- Python 3.12
- aiogram 3.x (Telegram Bot API)
- ChromaDB (векторная база данных)
- Redis (кеширование и состояния)
- PostgreSQL (хранение данных)
- Docker & Docker Compose
- Sentence Transformers (embeddings)
- Qwen 2.5 (языковая модель)

## Требования

- Docker и Docker Compose
- Git
- Не менее 4GB RAM
- Python 3.12 (для локальной разработки)

## Установка и запуск

1. Клонирование репозитория:
```bash
git clone https://github.com/Xpos587/pfd-aiogram-2024
cd pfd-aiogram-2024
```

2. Настройка переменных окружения:
```bash
cp .env.dist .env
```
Отредактируйте файл `.env`, установив необходимые значения:
- `BOT_TOKEN` - токен вашего Telegram бота (получить у @BotFather)
- `ADMIN_IDS` - ID администраторов бота
- Настройки подключения к базам данных
- Конфигурация API моделей

3. Запуск с помощью Docker Compose:
```bash
docker compose up -d
```

4. Проверка работоспособности:
```bash
docker compose ps
```

## Локальная разработка

1. Создание виртуального окружения:
```bash
conda env create -f environment.yml
conda activate default
```

2. Установка зависимостей:
```bash
pip install -r requirements.txt
```

3. Применение миграций базы данных:
```bash
make migrate
```

4. Запуск бота:
```bash
make run
```

## Структура проекта

```
├── bot/                    # Основной код бота
│   ├── handlers/          # Обработчики команд
│   ├── keyboards/         # Клавиатуры
│   ├── filters/          # Фильтры сообщений
│   └── middlewares/      # Промежуточные обработчики
├── services/             # Бизнес-логика
│   ├── database/        # Работа с БД
│   └── qna/            # Логика вопросов-ответов
├── migrations/          # Миграции базы данных
└─── locales/            # Файлы локализации
```

## Команды разработки

- `make lint` - проверка кода
- `make reformat` - форматирование кода
- `make i18n` - обновление переводов
- `make migration message="Migration message"` - создание миграции
- `make migrate` - применение миграций
- `make rollback` - откат последней миграции
- `make run` - запуск бота

## Лицензия

MIT License

## Авторы

- [Xpos587](https://github.com/Xpos587)

## Поддержка

При возникновении проблем создавайте issue в репозитории проекта.
