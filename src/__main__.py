import asyncio
import logging
import os

import chromadb
import chromadb.config

from src.config import CHROMA_HOST, CHROMA_PORT, KNOWLEDGE_BASE_PATH
from src.document_processor import process_document
from src.knowledge_base_watcher import run_knowledge_base_watcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def initial_load(path: str, chroma_client: chromadb.AsyncClientAPI):
    logger.info("Начало начальной загрузки документов")
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                await process_document(file_path, chroma_client)
                logger.info(f"Загружен файл: {file_path}")
            except Exception as e:
                logger.error(f"Ошибка при загрузке файла {file_path}: {str(e)}")
    logger.info("Начальная загрузка документов завершена")


async def main():
    # Инициализация клиента Chroma
    chroma_client = await chromadb.AsyncHttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        settings=chromadb.config.Settings(anonymized_telemetry=False),
    )

    # Начальная загрузка всех документов
    await initial_load(KNOWLEDGE_BASE_PATH, chroma_client)

    # Запуск отслеживания изменений
    try:
        await run_knowledge_base_watcher(chroma_client)
    except asyncio.CancelledError:
        logger.info("Наблюдатель базы знаний остановлен")
    except Exception as e:
        logger.error(f"Ошибка в наблюдателе базы знаний: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
