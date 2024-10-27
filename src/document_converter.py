import asyncio
import logging
import os
from typing import Dict

import aiofiles
import pymupdf4llm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def office_to_pdf(file_path: str) -> str:
    output_dir = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    pdf_file = os.path.join(output_dir, os.path.splitext(base_name)[0] + ".pdf")

    try:
        process = await asyncio.create_subprocess_exec(
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            file_path,
            "--outdir",
            output_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(
                f"Error converting {file_path} to PDF: {stderr.decode()}"
            )
            raise RuntimeError(f"Failed to convert {file_path} to PDF")

        logger.info(f"Successfully converted {file_path} to PDF")
        return pdf_file
    except Exception as e:
        logger.error(f"Error in office_to_pdf: {str(e)}")
        raise


async def read_markdown_file(file_path: str) -> str:
    try:
        async with aiofiles.open(file_path, mode="r") as file:
            content = await file.read()
        return content
    except Exception as e:
        logger.error(f"Error reading markdown file {file_path}: {str(e)}")
        raise


async def convert_to_markdown(file_path: str) -> Dict[str, str]:
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    metadata = {
        "original_file": file_path,
        "file_type": ext[1:],  # Убираем точку из расширения
        "conversion_method": "",
    }

    converters = {
        (".doc", ".docx", ".rtf"): lambda f: (
            pymupdf4llm.to_markdown(
                f,
                write_images=False,
                embed_images=False,
                graphics_limit=None,
                margins=(0, 0, 0, 0),
                table_strategy="lines_strict",
                fontsize_limit=1,
                ignore_code=True,
                show_progress=False,
            ),
            "office_to_pdf",
        ),
        ".pdf": lambda f: (
            pymupdf4llm.to_markdown(
                f,
                write_images=False,
                embed_images=False,
                graphics_limit=None,
                margins=(0, 0, 0, 0),
                table_strategy="lines_strict",
                fontsize_limit=1,
                ignore_code=True,
                show_progress=False,
            ),
            "direct_pdf",
        ),
        ".md": read_markdown_file,
    }

    try:
        if ext in (".doc", ".docx", ".rtf"):
            pdf_file = await office_to_pdf(file_path)
            content, method = converters[".pdf"](pdf_file)
        elif ext == ".md":
            content = await converters[".md"](file_path)
            method = "direct_markdown"
        elif ext == ".pdf":
            content, method = converters[".pdf"](file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

        metadata["conversion_method"] = method
        logger.info(f"Successfully converted {file_path} to markdown")
        return {"content": content, "metadata": metadata}
    except Exception as e:
        logger.error(f"Error converting {file_path} to markdown: {str(e)}")
        raise


async def process_file(file_path: str) -> Dict[str, str]:
    try:
        return await convert_to_markdown(file_path)
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        raise
