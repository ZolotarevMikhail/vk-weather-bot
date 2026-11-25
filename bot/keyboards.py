"""Клавиатуры бота: главная менюшка с кнопками урока."""

import json

from vkbottle import Keyboard, KeyboardButtonColor, Text

#: Кнопки главного меню: подпись -> (цвет)
MENU_BUTTONS = [
    ("🌤 Погода сейчас", "primary"),
    ("📅 Прогноз 5 дней", "primary"),
    ("⚖️ Сравнение городов", "secondary"),
    ("🌫 Расширенный режим", "secondary"),
    ("📍 Геолокация", "positive"),
    ("🏙 Мой город", "secondary"),
    ("ℹ️ Помощь", "secondary"),
]

# payload кнопок — VK-канонический формат
# (VK-доки: payload обязателен для text-кнопок)
MENU_PAYLOADS = tuple(
    json.dumps({"cmd": name})
    for name in (
        "weather_now",
        "forecast5",
        "compare",
        "extended",
        "geo",
        "my_city",
        "help",
    )
)

#: Кнопка-псевдоним «назад в меню» (та же клавиатура возвращается ответом)
MENU_TITLE = "Главное меню погодного бота"


def build_main_keyboard() -> str:
    """Собрать главную клавиатуру: 2 кнопки в ряд, JSON для VK."""
    keyboard = Keyboard(one_time=False, inline=False)
    colors = {
        "primary": KeyboardButtonColor.PRIMARY,
        "positive": KeyboardButtonColor.POSITIVE,
        "secondary": KeyboardButtonColor.SECONDARY,
    }
    for index, (label, color) in enumerate(MENU_BUTTONS):
        # vkbottle 4.11: цвет кнопки — аргумент add(), метод .color()
        # у кнопок удалён; payload — VK-канонический формат, без него
        # клиенты могут терять клавиатуру
        keyboard.add(
            Text(label, payload=MENU_PAYLOADS[index]), color=colors[color]
        )
        if index % 2 == 1 and index < len(MENU_BUTTONS) - 1:
            keyboard.row()
    return keyboard.get_json()


MAIN_KEYBOARD = build_main_keyboard()


def menu_with_hint() -> str:
    """Вернуть текст-шапку меню (клавиатура передаётся рядом)."""
    return "Выберите действие кнопкой ниже:"


#: Справка по функциям бота
HELP_TEXT = (
    "Я — погодный бот из урока VPd04.\n"
    "• 🌤 Погода сейчас — погода города по названию\n"
    "• 📅 Прогноз 5 дней — сводка с шагом 3 часа (сгруппирована по дням)\n"
    "• ⚖️ Сравнение городов — введите два города через запятую\n"
    "• 🌫 Расширенный режим — давление, видимость, качество воздуха\n"
    "• 📍 Геолокация — отправьте точку на карте или координаты "
    "текстом: 55.7558, 37.6173\n"
    "• 🏙 Мой город — погода последнего запрошенного города"
)
