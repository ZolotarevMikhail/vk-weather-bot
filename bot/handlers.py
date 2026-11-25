"""Обработчики сообщений бота: меню, состояния FSM, гео, сравнение городов.

Каждая кнопка меню ставит состояние ожидания; следующий текст пользователя
обрабатывается по состоянию. Ошибки погоды показываются словом, без падений.
"""

import logging

from vkbottle import GeoRule
from vkbottle.bot import Bot, Message

from weather_api import utils
from weather_api.client import OpenWeatherAPI
from weather_api.exceptions import OpenWeatherAPIError

from bot.keyboards import HELP_TEXT, MAIN_KEYBOARD, MENU_BUTTONS
from bot.states import WeatherStates

logger = logging.getLogger("weather-bot")

#: клиент погоды — один на весь бот, ключ из .env
weather_client = OpenWeatherAPI()

#: последний запрошенный город (peer_id -> название)
last_city_by_peer: dict[int, str] = {}

#: подписи кнопок меню — чтобы state-обработчики их пропускали
MENU_LABELS = {label for label, _color in MENU_BUTTONS}


def remember_city(peer_id: int, city: str) -> None:
    """Запомнить последний город пользователя."""
    last_city_by_peer[peer_id] = city


async def finish_and_answer(
    bot: Bot, message: Message, text: str
) -> None:
    """Снять состояние и ответить текстом с главной клавиатурой."""
    if message.state_peer:
        await bot.state_dispenser.delete(message.peer_id)
    await message.answer(text, keyboard=MAIN_KEYBOARD)


async def answer_weather(message: Message, extended: bool) -> str:
    """Собрать текст погоды по городу из сообщения."""
    city = message.text.strip()
    remember_city(message.peer_id, city)
    packed = weather_client.get_weather_by_city(city, extended=extended)
    weather = packed["weather"]
    if extended and packed.get("air"):
        return utils.format_extended_weather(weather, packed["air"])
    return utils.format_basic_weather(weather)


def extract_geo_coordinates(message: Message):
    """Достать широту и долготу из геолокации сообщения, если она есть."""
    geo = getattr(message, "geo", None)
    coordinates = getattr(geo, "coordinates", None) if geo else None
    if coordinates is None:
        return None
    return coordinates.latitude, coordinates.longitude


def register_handlers(bot: Bot) -> None:
    """Зарегистрировать все обработчики: порядок важен — меню выше состояний."""

    @bot.on.message(text="🌤 Погода сейчас")
    async def ask_weather_city(message: Message):
        await finish_and_answer(bot, message, "Введите город:")

    @bot.on.message(text="📅 Прогноз 5 дней")
    async def ask_forecast_city(message: Message):
        await finish_and_answer(bot, message, "Введите город:")

    @bot.on.message(text="🌫 Расширенный режим")
    async def ask_extended_city(message: Message):
        await finish_and_answer(
            bot,
            message,
            "Введите город: пришлю давление, видимость и качество воздуха.",
        )

    @bot.on.message(text="⚖️ Сравнение городов")
    async def ask_compare_cities(message: Message):
        await finish_and_answer(
            bot,
            message,
            "Введите два города через запятую, например: Москва, Сочи",
        )

    @bot.on.message(text="📍 Геолокация")
    async def ask_geo(message: Message):
        await finish_and_answer(
            bot,
            message,
            "Прикрепите точку на карте (скрепка → Геолокация) в этом чате "
            "или пришлите координаты текстом: 55.7558, 37.6173",
        )

    @bot.on.message(text="ℹ️ Помощь")
    async def show_help(message: Message):
        await finish_and_answer(bot, message, HELP_TEXT)

    @bot.on.message(text="🏙 Мой город")
    async def show_last_city(message: Message):
        city = last_city_by_peer.get(message.peer_id)
        if not city:
            await finish_and_answer(
                bot, message, "Я ещё не запоминал вашего города. Введите его:"
            )
            await bot.state_dispenser.set(
                message.peer_id, WeatherStates.WAITING_WEATHER_CITY
            )
            return
        try:
            packed = weather_client.get_weather_by_city(city)
            await finish_and_answer(
                bot, message, utils.format_basic_weather(packed["weather"])
            )
        except OpenWeatherAPIError as error:
            await finish_and_answer(bot, message, f"Ошибка: {error}")

    @bot.on.message(GeoRule())
    async def weather_by_geo(message: Message):
        coordinates = extract_geo_coordinates(message)
        if coordinates is None:
            await finish_and_answer(
                bot, message, "Не удалось прочитать геолокацию сообщения."
            )
            return
        latitude, longitude = coordinates
        try:
            packed = weather_client.get_weather_by_coordinates(
                latitude, longitude
            )
            await finish_and_answer(
                bot, message, utils.format_basic_weather(packed["weather"])
            )
        except OpenWeatherAPIError as error:
            await finish_and_answer(bot, message, f"Ошибка: {error}")

    @bot.on.message(state=WeatherStates.WAITING_WEATHER_CITY)
    async def city_weather(message: Message):
        if message.text.strip() in MENU_LABELS:
            return
        try:
            text = await answer_weather(message, extended=False)
            await finish_and_answer(bot, message, text)
        except OpenWeatherAPIError as error:
            await message.answer(
                f"Ошибка: {error}. Введите город ещё раз:"
            )

    @bot.on.message(state=WeatherStates.WAITING_FORECAST_CITY)
    async def city_forecast(message: Message):
        if message.text.strip() in MENU_LABELS:
            return
        try:
            forecast = weather_client.get_forecast_by_city(
                message.text.strip()
            )
            remember_city(message.peer_id, message.text.strip())
            await finish_and_answer(bot, message, utils.format_forecast(forecast))
        except OpenWeatherAPIError as error:
            await message.answer(
                f"Ошибка: {error}. Введите город ещё раз:"
            )

    @bot.on.message(state=WeatherStates.WAITING_EXTENDED_CITY)
    async def city_extended(message: Message):
        if message.text.strip() in MENU_LABELS:
            return
        try:
            text = await answer_weather(message, extended=True)
            await finish_and_answer(bot, message, text)
        except OpenWeatherAPIError as error:
            await message.answer(
                f"Ошибка: {error}. Введите город ещё раз:"
            )

    @bot.on.message(state=WeatherStates.WAITING_COMPARE_CITIES)
    async def compare_cities(message: Message):
        if message.text.strip() in MENU_LABELS:
            return
        parts = [part.strip() for part in message.text.split(",")]
        if len(parts) != 2 or not all(parts):
            await finish_and_answer(
                bot,
                message,
                "Нужны ровно два города через запятую, "
                "например: Москва, Сочи",
            )
            return
        try:
            first = weather_client.get_weather_by_city(parts[0])
            second = weather_client.get_weather_by_city(parts[1])
            remember_city(message.peer_id, parts[1])
            text = utils.format_city_comparison(first, second)
            await finish_and_answer(bot, message, text)
        except OpenWeatherAPIError as error:
            await message.answer(
                f"Ошибка: {error}. Повторите запрос: Москва, Сочи"
            )

    @bot.on.message()
    async def fallback(message: Message):
        if message.state_peer:
            await bot.state_dispenser.delete(message.peer_id)
        await message.answer(
            "Я не понял сообщение. Начните с меню ниже:",
            keyboard=MAIN_KEYBOARD,
        )
