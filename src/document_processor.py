import asyncio
import hashlib
import logging
import os
import re
from typing import Dict, List

import chromadb
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer

from src.config import CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME
from src.document_converter import process_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: str) -> str:
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)
    return file_hash.hexdigest()


async def preprocess_markdown(markdown_content: str) -> str:
    clean_content = markdown_content.lower()
    clean_content = re.sub(r"<!--.*?-->", "", clean_content, flags=re.DOTALL)
    clean_content = re.sub(r"[^\w\s.,;:?!-]", " ", clean_content)
    clean_content = re.sub(r"\s+", " ", clean_content).strip()
    return clean_content


def extract_section_numbers(content: str) -> List[str]:
    # Это регулярное выражение ищет номера секций в форматах типа "1.", "1.1.", "1.1.1." и т.д.
    section_pattern = r"(?<!\d)(\d+(\.\d+)*)(?=\s)"
    return re.findall(section_pattern, content)


async def split_into_chunks(
    clean_content: str, chunk_size: int = 500
) -> List[Dict[str, str]]:
    sentences = re.split(r"(?<=[.!?])\s+", clean_content)
    chunks = []
    current_chunk = []
    current_length = 0
    current_section = ""

    for sentence in sentences:
        section_numbers = extract_section_numbers(sentence)
        if section_numbers:
            current_section = section_numbers[0]

        if current_length + len(sentence) > chunk_size and current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                {
                    "text": chunk_text,
                    "start_index": clean_content.index(chunk_text),
                    "end_index": clean_content.index(chunk_text)
                    + len(chunk_text),
                    "section": current_section,
                }
            )
            current_chunk = []
            current_length = 0
        current_chunk.append(sentence)
        current_length += len(sentence)

    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append(
            {
                "text": chunk_text,
                "start_index": clean_content.index(chunk_text),
                "end_index": clean_content.index(chunk_text) + len(chunk_text),
                "section": current_section,
            }
        )

    return chunks


async def create_embeddings(
    chunks: List[Dict[str, str]],
    model_name: str = EMBEDDING_MODEL_NAME,
    batch_size: int = 8,
) -> List[List[float]]:
    model = SentenceTransformer(model_name)

    embeddings = []

    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        batch_chunks = [chunk["text"] for chunk in chunks[start:end]]
        batch_embeddings = await asyncio.to_thread(
            model.encode,
            batch_chunks,
            batch_size=batch_size,
            show_progress_bar=True,
        )
        embeddings.extend(batch_embeddings)

    return embeddings


async def upsert_to_chroma(
    embeddings: List[List[float]],
    chunks: List[Dict[str, str]],
    metadata: Dict[str, str],
    collection: Collection,
    file_hash: str,
):
    ids = [f"{file_hash}_{i}" for i in range(len(chunks))]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            **metadata,
            "chunk_start": chunk["start_index"],
            "chunk_end": chunk["end_index"],
            "chunk_index": i,
        }
        for i, chunk in enumerate(chunks)
    ]

    await collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


async def process_document(
    file_path: str, chroma_client: chromadb.AsyncClientAPI
):
    try:
        logger.info(f"Processing document: {file_path}")

        file_hash = calculate_file_hash(file_path)
        last_modified = os.path.getmtime(file_path)

        collection = await chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME
        )

        # Проверяем, есть ли уже документ с таким хешем
        existing_docs = await collection.get(where={"file_hash": file_hash})
        if existing_docs["ids"]:
            existing_doc = existing_docs["metadatas"][0]
            if existing_doc["last_modified"] == last_modified:
                logger.info(f"Документ {file_path} не изменился, пропускаем")
                return
            logger.info(f"Документ {file_path} изменился, обновляем")
        else:
            logger.info(f"Добавляем новый документ {file_path}")

        conversion_result = await process_file(file_path)
        markdown_content = conversion_result["content"]
        metadata = conversion_result["metadata"]

        clean_content = await preprocess_markdown(markdown_content)
        chunks = await split_into_chunks(clean_content)

        # Получаем существующие чанки для этого документа
        existing_chunks = await collection.get(where={"file_path": file_path})

        # Сравниваем новые чанки с существующими и обновляем только измененные
        chunks_to_update = []
        for chunk in chunks:
            existing_chunk = next(
                (
                    ec
                    for ec in existing_chunks["documents"]
                    if ec["section"] == chunk["section"]
                ),
                None,
            )
            if not existing_chunk or existing_chunk["text"] != chunk["text"]:
                chunks_to_update.append(chunk)

        if chunks_to_update:
            embeddings = await create_embeddings(chunks_to_update)
            await upsert_to_chroma(
                embeddings, chunks_to_update, metadata, collection, file_hash
            )

        logger.info(f"Document processed successfully: {file_path}")
    except Exception as e:
        logger.error(f"Error processing document {file_path}: {str(e)}")
        raise
