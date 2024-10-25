import base64
from csv import DictReader
from os import PathLike
from typing import Any, Literal, Optional, Union

import aiohttp
from aiogram import Bot
from yaml import safe_load


def assets(dir: Literal["yaml", "image", "csv"], item: str) -> str:
    """
    Generate a file path for assets in specified directories.

    Args:
    - dir (Literal["yaml", "image", "csv"]): The directory name.
    - item (str): The name of the file in the directory.

    Returns:
    - str: The relative path to the asset.
    """
    return f"./assets/{dir}/{item}"


async def get_content(bot: Bot, file_id: str) -> Optional[bytes]:
    """
    Retrieve file content from Telegram using a file ID.

    Args:
    - bot (Bot): The Telegram Bot instance.
    - file_id (str): The unique identifier for the file on Telegram.

    Returns:
    - Optional[bytes]: The file content as bytes if successful, None otherwise.
    """
    file = await bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

    async with aiohttp.ClientSession() as session, session.get(
        file_url
    ) as response:
        if response.status == 200:
            return await response.read()
        return None


async def image_to_base64(image_bytes: bytes) -> str:
    """
    Convert image bytes to a base64 encoded string.

    Args:
    - image_bytes (bytes): The raw bytes of the image.

    Returns:
    - str: The base64 encoded string of the image.
    """
    encoded_string = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded_string}"


def load_yaml(input_data: Union[str, bytes, PathLike[str]]) -> dict[Any, Any]:
    """
    Load a YAML file or raw bytes into a Python dictionary.

    Args:
    - input_data (Union[str, bytes, PathLike]): The path to
    the YAML file or raw YAML bytes.

    Returns:
    - dict: The loaded YAML data as a dictionary.
    """
    # Checking if the input argument is a file path
    if isinstance(input_data, (str, PathLike)):
        with open(input_data, "r", encoding="utf-8") as file:
            return dict(safe_load(file))

    # Checking if the input argument is a byte object
    elif isinstance(input_data, bytes):
        return dict(safe_load(input_data.decode("utf-8")))

    else:
        raise ValueError("Invalid input type. Expected a file path or bytes.")


def load_csv(
    input_data: Union[str, bytes, PathLike[str]], delimiter: str = ","
) -> list[dict[str, str]]:
    """
    Load a CSV file or raw bytes into a list of dictionaries.

    Args:
    - input_data (Union[str, bytes, PathLike]): The
    path to the CSV file or raw CSV bytes.

    Returns:
    - list[dict[str, str]]: A list of dictionaries with keys as column headers.
    """
    # Checking if the input argument is a file path
    if isinstance(input_data, (str, PathLike)):
        with open(input_data, "r", encoding="utf-8") as file:
            return list(DictReader(file, delimiter=delimiter))

    # Checking if the input argument is a byte object
    elif isinstance(input_data, bytes):
        return list(
            DictReader(
                input_data.decode("utf-8").splitlines(),
                delimiter=delimiter,
            )
        )

    else:
        raise ValueError("Invalid input type. Expected a file path or bytes.")
