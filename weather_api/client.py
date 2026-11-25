"""Класс OpenWeatherAPI — клиент погодного сервиса для бота и консоли.

Endpoint'ы взяты дословно из документации OpenWeatherMap (урок VPd04).
Ключ и адреса — в weather_api/config.py, ключ не вписывается в код.
"""

import requests

from weather_api import config
from weather_api.exceptions import (
    APIConnectionError,
    CityNotFoundError,
    InvalidApiKeyError,
    OpenWeatherAPIError,
)

#: Шкала качества воздуха: пара «нижняя граница» компонента на каждый уровень.
#: Индекс 0 — верх Good, 1 — верх Fair, 2 — верх Moderate, 3 — верх Poor.
AIR_SCALE = {
    "so2": (20.0, 80.0, 250.0, 350.0),
    "no2": (40.0, 70.0, 150.0, 200.0),
    "pm10": (20.0, 50.0, 100.0, 200.0),
    "pm2_5": (10.0, 25.0, 50.0, 75.0),
    "o3": (60.0, 100.0, 140.0, 180.0),
    "co": (4400.0, 9400.0, 12400.0, 15400.0),
}

#: Названия уровней качества воздуха по убыванию
AIR_LEVELS = ("Хорошее", "Приемлемое", "Умеренное", "Плохое", "Очень плохое")

#: Совет человеку для каждого уровня воздуха
AIR_ADVICE = {
    "Хорошее": "Качество воздуха хорошее, все показатели в безопасной зоне.",
    "Приемлемое": (
        "Воздух приемлемый, но отдельные показатели слегка повышены."
    ),
    "Умеренное": (
        "Воздух умеренный: дольше часа активности на улице не стоит "
        "планировать чувствительным группам."
    ),
    "Плохое": (
        "Воздух плохой: чувствительным группам стоит сократить прогулки "
        "и открыть окна меньше."
    ),
    "Очень плохое": (
        "Воздух очень плохой: высокий риск для здоровья, на улицу только "
        "по необходимости."
    ),
}


class OpenWeatherAPI:
    """Собирает запросы к OpenWeatherMap и переводит ответ в данные.

    Вход: город или координаты. Выход: словари с данными и текстами,
    готовыми для консоли и бота (форматирование в weather_api/utils).
    """

    #: Таймаут запроса, сек
    TIMEOUT = config.REQUEST_TIMEOUT
    #: Отправлять язык и единицы на русском
    LANG = config.RESPONSE_LANG
    UNITS = config.RESPONSE_UNITS

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or config.OPENWEATHER_API_KEY
        if not self.api_key:
            raise OpenWeatherAPIError(
                "Ключ OpenWeather не задан: "
                "заполните OPENWEATHER_API_KEY в .env"
            )
        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: dict) -> dict:
        """Отправить GET-запрос к endpoint'у и вернуть словарь ответа."""
        params = dict(params)
        params["appid"] = self.api_key
        params["lang"] = self.LANG
        params["units"] = self.UNITS
        try:
            response = self.session.get(
                endpoint, params=params, timeout=self.TIMEOUT
            )
        except requests.Timeout as exc:
            raise APIConnectionError(
                "OpenWeather не успел ответить, повторите позже"
            ) from exc
        except requests.RequestException as exc:
            raise APIConnectionError(
                "Сеть недоступна, проверьте подключение"
            ) from exc

        body = self._parse_body(response)
        if isinstance(body, list):
            # Геокодинг отвечает списком совпадений — кода ошибки внутри нет
            return body
        status_code = body.get("cod")
        if body.get("message") and status_code not in (200, "200"):
            self._raise_by_code(status_code, body["message"])
        return body

    def _parse_body(self, response: requests.Response) -> dict:
        """Разобрать JSON ответа; пустое тело — отдельная ошибка связи."""
        try:
            return response.json()
        except ValueError as exc:
            raise APIConnectionError(
                "OpenWeather вернул непонятный ответ"
            ) from exc

    def _raise_by_code(self, status_code, message: str) -> None:
        """Перевести код ошибки API в своё понятное исключение."""
        if status_code in (401, "401"):
            raise InvalidApiKeyError(
                "Невалидный API-ключ OpenWeather (проверьте .env)"
            )
        if status_code in (404, "404"):
            raise CityNotFoundError()
        raise OpenWeatherAPIError(f"OpenWeather ответил ошибкой: {message}")

    def _direct_geocode(self, city: str) -> dict:
        """Прямой геокодинг: название -> координаты первого совпадения."""
        body = self._make_request(
            config.ENDPOINTS["geocode"],
            {"q": city, "limit": 1},
        )
        if not body:
            raise CityNotFoundError(
                f"Город «{city}» не найден, проверьте название"
            )
        return body[0]

    def _reverse_geocode(self, lat: float, lon: float) -> dict:
        """Обратный геокодинг: координаты -> название места."""
        body = self._make_request(
            config.ENDPOINTS["reverse_geocode"],
            {"lat": lat, "lon": lon, "limit": 1},
        )
        if not body:
            raise CityNotFoundError(
                "По этим координатам место не определено"
            )
        return body[0]

    def _current_weather(self, lat: float, lon: float) -> dict:
        """Текущая погода по координатам."""
        return self._make_request(
            config.ENDPOINTS["current"], {"lat": lat, "lon": lon}
        )

    def _forecast_weather(self, lat: float, lon: float) -> dict:
        """Прогноз с шагом 3 часа на 5 дней по координатам."""
        return self._make_request(
            config.ENDPOINTS["forecast"], {"lat": lat, "lon": lon}
        )

    def _air_pollution(self, lat: float, lon: float) -> dict:
        """Загрязнение воздуха по координатам."""
        return self._make_request(
            config.ENDPOINTS["air_pollution"], {"lat": lat, "lon": lon}
        )

    def _analyze_air_quality(self, air_data: dict) -> dict:
        """Оценить воздух по шкале урока: метка, превышения, совет."""
        entry = air_data["list"][0]
        components = entry["components"]
        level_scores = []
        exceeders = []
        for code in AIR_SCALE:
            if code not in components:
                continue
            value = components[code]
            upper_good, upper_fair, upper_moderate, upper_poor = (
                AIR_SCALE[code]
            )
            if value < upper_good:
                scores = 0
            elif value < upper_fair:
                scores = 1
            elif value < upper_moderate:
                scores = 2
            elif value < upper_poor:
                scores = 3
            else:
                scores = 4
            level_scores.append(scores)
            if scores > 0:
                exceeders.append(
                    f"{code.upper().replace('_', '.')} ({value})"
                )

        level = AIR_LEVELS[max(level_scores)]
        return {
            "aqi": entry["main"]["aqi"],
            "label": level,
            "summary": AIR_ADVICE[level],
            "exceeders": exceeders,
        }

    def get_weather_by_city(
        self, city: str, extended: bool = False
    ) -> dict:
        """Погода по названию города; extended добавляет воздух и детали."""
        place = self._direct_geocode(city)
        coords_key = {"lat": place["lat"], "lon": place["lon"]}
        result = self._current_weather(**coords_key)
        return self._pack_weather(result, extended, coords_key)

    def get_weather_by_coordinates(
        self, lat: float, lon: float, extended: bool = False
    ) -> dict:
        """Погода по координатам; название места подставляется геокодингом."""
        result = self._current_weather(lat=lat, lon=lon)
        if not result.get("name"):
            place = self._reverse_geocode(lat, lon)
            result["name"] = place.get("name", "неизвестное место")
        return self._pack_weather(result, extended, {"lat": lat, "lon": lon})

    def get_forecast_by_city(
        self, city: str, extended: bool = False
    ) -> dict:
        """Прогноз на 5 дней по названию города."""
        place = self._direct_geocode(city)
        forecast = self._forecast_weather(lat=place["lat"], lon=place["lon"])
        return forecast

    def _pack_weather(
        self, weather: dict, extended: bool, coords: dict
    ) -> dict:
        """Упаковать ответ погоды и, при extended, анализ воздуха."""
        packed = {"weather": weather, "coords": coords, "extended": extended}
        if extended:
            air = self._air_pollution(**coords)
            packed["air"] = self._analyze_air_quality(air)
        return packed
