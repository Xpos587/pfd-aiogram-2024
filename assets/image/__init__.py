import os

from aiogram.types import FSInputFile

base_dir = os.path.abspath(os.path.dirname(__file__))


def load(path: str) -> FSInputFile:
    return FSInputFile(os.path.join(base_dir, path))


start = load("start.png")
faq = load("faq.png")
chat = load("chat.png")
