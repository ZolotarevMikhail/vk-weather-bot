"""Состояния бота: что именно ждём от пользователя (FSM).

Бот задаёт состояние после клика по кнопке, а следующий текстовый
пост обработчик по состоянию. Состояние снимается после ответа.
"""

from vkbottle import BaseStateGroup


class WeatherStates(BaseStateGroup):
    """Все ожидания ввода пользователя."""

    WAITING_WEATHER_CITY = 1
    WAITING_FORECAST_CITY = 2
    WAITING_EXTENDED_CITY = 3
    WAITING_COMPARE_CITIES = 4
