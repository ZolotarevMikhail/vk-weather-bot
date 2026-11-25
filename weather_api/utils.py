"""Форматирование ответов OpenWeather в человекочитаемый текст на русском."""

import datetime

#: Метки компонентов воздуха: код -> русское название
POLLUTANT_NAMES = {
    "so2": "SO2",
    "no2": "NO2",
    "pm10": "PM10",
    "pm2_5": "PM2.5",
    "o3": "O3",
    "co": "CO",
}

#: Порядок компонентов, принятый в шкале урока
POLLUTANT_ORDER = ("so2", "no2", "pm10", "pm2_5", "o3", "co")


def temperature_str(value: float) -> str:
    """Вернуть температуру со знаком, вида '+21°'."""
    rounded = round(value)
    sign = "+" if rounded > 0 else ("" if rounded == 0 else "-")
    return f"{sign}{abs(rounded)}°"


def format_basic_weather(data: dict) -> str:
    """Собрать краткую сводку текущей погоды."""
    main = data["main"]
    weather = data["weather"][0]["description"]
    wind = data["wind"]["speed"]
    lines = [
        f"🌍 {data['name']}: {weather}",
        f"🌡 Температура: {temperature_str(main['temp'])} "
        f"(ощущается как {temperature_str(main['feels_like'])})",
        f"💧 Влажность: {main['humidity']}%",
        f"💨 Ветер: {round(wind, 1)} м/с",
        f"☁️ Облачность: {data['clouds']['all']}%",
    ]
    return "\n".join(lines)


def format_extended_weather(data: dict, air_analysis: dict) -> str:
    """Собрать расширенную сводку: база + давление, свет, качество воздуха."""
    sys_data = data["sys"]
    sunrise = datetime.datetime.fromtimestamp(
        sys_data["sunrise"], datetime.timezone.utc
    ).strftime("%H:%M")
    sunset = datetime.datetime.fromtimestamp(
        sys_data["sunset"], datetime.timezone.utc
    ).strftime("%H:%M")
    lines = [format_basic_weather(data)]
    lines.append(
        f"🌅 Восход: {sunrise} UTC, 🌇 закат: {sunset} "
        f"(время API, без местного пояса)"
    )
    lines.append(f"⚖️ Давление: {data['main']['pressure']} гПа")
    if data.get("visibility") is not None:
        km = data["visibility"] / 1000
        lines.append(f"👁 Видимость: {round(km, 1)} км")
    lines.append(format_air_quality(air_analysis))
    return "\n".join(lines)


def format_air_quality(analysis: dict) -> str:
    """Собрать текст анализа воздуха: метка, превышения, совет."""
    lines = [
        f"🌫 Качество воздуха: {analysis['label']} (AQI {analysis['aqi']})",
        f"💬 {analysis['summary']}",
    ]
    if analysis["exceeders"]:
        listed = ", ".join(analysis["exceeders"])
        lines.append(f"📊 Выше нормы: {listed}")
    return "\n".join(lines)


def format_city_comparison(first: dict, second: dict) -> str:
    """Сравнить погоду двух городов: температура, влажность, ветер."""
    rows = [
        ("Температура", "temp", temperature_str, 1),
        ("Влажность", "humidity", (lambda value: f"{value}%"), 0),
        ("Ветер", "wind_speed", lambda value: f"{value} м/с", 1),
    ]
    name_first = first["weather"]["name"]
    name_second = second["weather"]["name"]
    lines = [f"⚖️ {name_first} vs {name_second}:"]
    for title, field, presenter, digits in rows:
        first_weather = first["weather"]
        second_weather = second["weather"]
        first_value = _pooled_value(first_weather, field)
        second_value = _pooled_value(second_weather, field)
        difference = round(first_value - second_value, digits)
        lines.append(
            f"• {title}: {name_first} {presenter(first_value)}, "
            f"{name_second} {presenter(second_value)}, "
            f"разница {difference:+g}"
        )
    return "\n".join(lines)


def _pooled_value(weather: dict, field: str) -> float:
    """Достать число для сравнения из ответа погоды по имени поля."""
    if field == "wind_speed":
        return round(weather["wind"]["speed"], 1)
    return float(weather["main"][field])


def format_forecast(data: dict) -> str:
    """Собрать сводку прогноза на 5 дней: день, диапазон температур, осадки."""
    city = data["city"]["name"]
    days: dict[str, dict] = {}
    for entry in data["list"]:
        day = entry["dt_txt"][:10]
        slot = days.setdefault(
            day,
            {
                "min": entry["main"]["temp"],
                "max": entry["main"]["temp"],
                "descriptions": [],
                "pop_max": 0.0,
            },
        )
        slot["min"] = min(slot["min"], entry["main"]["temp"])
        slot["max"] = max(slot["max"], entry["main"]["temp"])
        slot["pop_max"] = max(slot["pop_max"], entry.get("pop", 0.0))
        slot["descriptions"].append(entry["weather"][0]["description"])

    lines = [f"📅 Прогноз на 5 дней — {city}:"]
    for day, slot in days.items():
        date_info = datetime.date.fromisoformat(day).strftime("%d.%m")
        typical = max(set(slot["descriptions"]), key=slot["descriptions"].count)
        rain = round(slot["pop_max"] * 100)
        lines.append(
            f"• {date_info}; {temperature_str(slot['min'])}…"
            f"{temperature_str(slot['max'])}; {typical}; "
            f"вероятность осадков до {rain}%"
        )
    return "\n".join(lines)
