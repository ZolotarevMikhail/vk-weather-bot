"""Консольный тест погодного модуля (ДЗ VPd04, шаг «проверь в консоли»).

Запуск из папки задания (с активным venv):
    python cli.py Москва
    python cli.py Москва --extended    # + качество воздуха
    python cli.py Москва --forecast    # прогноз на 5 дней
    python cli.py 55.7558 37.6173      # погода по координатам
"""

import argparse
import sys

from weather_api import utils
from weather_api.client import OpenWeatherAPI
from weather_api.exceptions import OpenWeatherAPIError


def build_parser() -> argparse.ArgumentParser:
    """Собрать парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Тест OpenWeatherAPI: погода, прогноз, воздух"
    )
    parser.add_argument(
        "place",
        help="город (например, Москва) или широта и долгота через пробел",
        nargs="+",
    )
    parser.add_argument(
        "--extended", action="store_true", help="расширенный режим"
    )
    parser.add_argument(
        "--forecast", action="store_true", help="прогноз на 5 дней"
    )
    return parser


def try_print_weather(client: OpenWeatherAPI, args) -> None:
    """Запросить и напечатать данные; ошибку показать словом, без трейсбека."""
    try:
        if args.forecast:
            city = " ".join(args.place)
            forecast = client.get_forecast_by_city(city)
            print(utils.format_forecast(forecast))
            return
        if len(args.place) == 2 and _looks_like_coordinates(args.place):
            latitude, longitude = map(float, args.place)
            packed = client.get_weather_by_coordinates(
                latitude, longitude, extended=args.extended
            )
        else:
            city = " ".join(args.place)
            if args.forecast:
                forecast = client.get_forecast_by_city(city)
                print(utils.format_forecast(forecast))
                return
            packed = client.get_weather_by_city(city, extended=args.extended)
        _print_packed(packed, extended=args.extended)
    except OpenWeatherAPIError as error:
        print(f"Ошибка: {error}")
        sys.exit(1)


def _looks_like_coordinates(place: list) -> bool:
    """Отличить «55.75 37.61» от «Санкт-Петербург» (два слова)."""
    try:
        floats = [float(item) for item in place]
    except ValueError:
        return False
    return all(-180 <= value <= 180 for value in floats)


def _print_packed(packed: dict, extended: bool) -> None:
    """Напечатать погоду; при extended — база + воздух."""
    weather = packed["weather"]
    if extended and packed.get("air"):
        print(utils.format_extended_weather(weather, packed["air"]))
    else:
        print(utils.format_basic_weather(weather))


if __name__ == "__main__":
    parsed = build_parser().parse_args()
    api = OpenWeatherAPI()
    try_print_weather(api, parsed)
