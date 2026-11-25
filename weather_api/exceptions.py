"""Свои исключения погодного модуля.

Каждый тип ошибки — отдельный класс, чтобы бот и тесты
различали причины отказа и показывали человеку понятный текст.
"""


class OpenWeatherAPIError(Exception):
    """Базовая ошибка работы с OpenWeather API."""


class CityNotFoundError(OpenWeatherAPIError):
    """Город по названию не найден в геокодинге."""


class InvalidApiKeyError(OpenWeatherAPIError):
    """API-ключ не принят сервисом (401)."""


class APIConnectionError(OpenWeatherAPIError):
    """Сеть недоступна или сервис не ответил вовремя."""
