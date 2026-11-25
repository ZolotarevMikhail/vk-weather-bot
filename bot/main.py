"""Точка входа бота: собирает Bot и запускает Long Poll.

Запуск: python -m bot.main  (из папки проекта, venv активен)
В терминале появится «loop will be run forever» — бот работает.
"""

import logging

from bot.config import VK_BOT_TOKEN
from bot.handlers import register_handlers
from vkbottle.bot import Bot


def build_bot() -> Bot:
    """Собрать бота с токеном сообщества."""
    if not VK_BOT_TOKEN:
        raise SystemExit(
            "Токен ВК не задан: заполните VK_BOT_TOKEN в файле .env"
        )
    return Bot(VK_BOT_TOKEN)


def main() -> None:
    """Настроить лог, зарегистрировать обработчики и запустить polling."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    bot = build_bot()
    register_handlers(bot)
    bot.run_forever()


if __name__ == "__main__":
    main()
