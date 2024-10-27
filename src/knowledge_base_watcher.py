import asyncio
import logging
import os

import chromadb
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.config import CHROMA_COLLECTION_NAME, KNOWLEDGE_BASE_PATH
from src.document_processor import calculate_file_hash, process_document

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class KnowledgeBaseHandler(FileSystemEventHandler):
    chroma_client: chromadb.AsyncClientAPI

    def __init__(self, chroma_client: chromadb.AsyncClientAPI):
        self.chroma_client = chroma_client
        self.loop = asyncio.get_event_loop()

    def on_created(self, event):
        if not event.is_directory:
            self.loop.create_task(self.process_file(event.src_path))

    def on_modified(self, event):
        if not event.is_directory:
            self.loop.create_task(self.process_file(event.src_path))

    def on_deleted(self, event):
        if not event.is_directory:
            self.loop.create_task(self.remove_from_chroma(event.src_path))

    async def process_file(self, file_path):
        try:
            await process_document(file_path, self.chroma_client)
            logger.info(f"Обработан файл: {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {file_path}: {str(e)}")

    async def remove_from_chroma(self, file_path):
        try:
            file_hash = await calculate_file_hash(file_path)
            collection = await self.chroma_client.get_or_create_collection(
                CHROMA_COLLECTION_NAME
            )
            await collection.delete(where={"file_hash": file_hash})
            logger.info(f"Удален файл из базы знаний: {file_path}")
        except Exception as e:
            logger.error(
                f"Ошибка при удалении файла {file_path} из базы знаний: {str(e)}"
            )


async def watch_knowledge_base(chroma_client):
    event_handler = KnowledgeBaseHandler(chroma_client)
    observer = Observer()
    observer.schedule(event_handler, KNOWLEDGE_BASE_PATH, recursive=True)
    observer.start()
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        observer.stop()
    observer.join()


async def initial_load(chroma_client):
    logger.info("Начало начальной загрузки документов")
    for root, dirs, files in os.walk(KNOWLEDGE_BASE_PATH):
        for file in files:
            file_path = os.path.join(root, file)
            await process_document(file_path, chroma_client)
    logger.info("Начальная загрузка документов завершена")


async def run_knowledge_base_watcher(chroma_client):
    await initial_load(chroma_client)
    await watch_knowledge_base(chroma_client)
