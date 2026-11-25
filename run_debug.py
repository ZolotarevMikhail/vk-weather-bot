"""Отладочный запуск: шим логера vkbottle + честный traceback.

vkbottle 4.11: StyleAdapter не имеет .opt — при необработанном исключении
в задаче падает сам vkbottle (tools/_runner.py:36) и прячет настоящую
ошибку. Добавляем .opt, который печатает реальный traceback, и запускаем
бота обычной точкой входа bot.main:main.
"""

import sys
import traceback

import vkbottle.modules


def _opt(self, *args, **kwargs):
    """Замена logger.opt: при exception печатаем настоящий traceback."""
    exc = kwargs.get("exception")
    if exc is not None:
        traceback.print_exception(exc, file=sys.stderr)
    return self


vkbottle.modules.StyleAdapter.opt = _opt

from bot.main import main  # noqa: E402  импорт строго после шима

if __name__ == "__main__":
    main()
