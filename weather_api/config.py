"""Конфигурация погодного API: ключ и адреса endpoint'ов.

Ключ OpenWeather берётся из файла .env (переменная OPENWEATHER_API_KEY).
Адреса endpoint'ов прописаны дословно из документации OpenWeatherMap,
как требует урок VPd04: память нейросетей хранит устаревшие адреса.
"""

import os

from dotenv import load_dotenv

load_dotenv()

#: Ключ OpenWeatherMap из .env
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

BASE_URL = "https://api.openweathermap.org"

#: Endpoint'ы бесплатного тарифа (дословно из документации)
ENDPOINTS = {
    "current": f"{BASE_URL}/data/2.5/weather",
    "forecast": f"{BASE_URL}/data/2.5/forecast",
    "air_pollution": f"{BASE_URL}/data/2.5/air_pollution",
    "geocode": f"{BASE_URL}/geo/1.0/direct",
    "reverse_geocode": f"{BASE_URL}/geo/1.0/reverse",
}

#: Таймаут запроса, секунды
REQUEST_TIMEOUT = 10

#: Язык описаний погоды в ответах API
RESPONSE_LANG = "ru"

#: Единицы измерения — метрические (°C, м/с)
RESPONSE_UNITS = "metric"
