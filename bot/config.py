"""Конфигурация бота: токен сообщества ВКонтакте из .env."""

import os

from dotenv import load_dotenv

load_dotenv()

#: LongPoll-токен сообщества (урок VPd04: Управление → Работа с API)
VK_BOT_TOKEN = os.getenv("VK_BOT_TOKEN", "")
