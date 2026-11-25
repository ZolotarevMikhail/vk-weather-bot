"""Погодный модуль: класс OpenWeatherAPI + форматирование ответов."""

from weather_api.client import OpenWeatherAPI
from weather_api.exceptions import (
    APIConnectionError,
    CityNotFoundError,
    InvalidApiKeyError,
    OpenWeatherAPIError,
)

__all__ = [
    "OpenWeatherAPI",
    "OpenWeatherAPIError",
    "CityNotFoundError",
    "InvalidApiKeyError",
    "APIConnectionError",
]
