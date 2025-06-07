import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import set_city, set_notify_times, get_user_settings
from weather_api import get_current_weather, get_forecast_5days
from scheduler import scheduler, send_daily_weather

router = Router()

# Стани FSM
class CityState(StatesGroup):
    waiting_for_city = State()

class NotifyTimeState(StatesGroup):
    waiting_for_times = State()

# Клавіатури
def main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌦 Дізнатися погоду", callback_data="menu_weather")],
        [InlineKeyboardButton(text="🏙 Встановити місто", callback_data="menu_set_city")],
        [InlineKeyboardButton(text="⏰ Встановити сповіщення", callback_data="menu_set_notify")]
    ])
    return kb

def weather_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌤 Погода зараз", callback_data="weather_current"),
         InlineKeyboardButton(text="📅 Прогноз на 5 днів", callback_data="weather_5days")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_main")]
    ])
    return kb

# Обробники команд
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "👋 *Вітаю!*\n\n"
        "Я — ваш погодний бот, який допоможе дізнатися поточну погоду 🌤 "
        "і отримати прогноз на 5 днів 📅.\n\n"
        "Також можу надсилати щоденні сповіщення з інформацією про погоду ⏰.\n\n"
        "Оберіть, що хочете зробити:"
    )
    await message.answer(welcome_text, reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "back_to_main")
async def callback_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Оберіть дію:", reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "menu_weather")
async def callback_menu_weather(call: CallbackQuery):
    await call.message.edit_text("Оберіть, яку погоду показати:", reply_markup=weather_menu_keyboard())

@router.callback_query(F.data == "menu_set_city")
async def callback_menu_set_city(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введіть назву міста (наприклад: Київ, Охтирка, Ужгород через кому).")
    await state.set_state(CityState.waiting_for_city)

@router.callback_query(F.data == "menu_set_notify")
async def callback_menu_set_notify(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Вкажіть часи у форматі HH:MM через кому (24-годинний). Приклад: 15:00, 18:00")
    await state.set_state(NotifyTimeState.waiting_for_times)

@router.callback_query(F.data == "weather_current")
async def callback_weather_current(call: CallbackQuery):
    user_id = call.from_user.id
    city, _ = get_user_settings(user_id)
    if not city:
        await call.message.edit_text("Спочатку потрібно встановити місто!", reply_markup=main_menu_keyboard())
        return
    # Розбиваємо на кілька міст, якщо введено через кому
    cities = [c.strip() for c in city.split(",") if c.strip()]
    weather_texts = []
    for c in cities:
        if c:  # Перевіряємо, чи місто не порожнє
            weather_text = await get_current_weather(c)
            weather_texts.append(weather_text)
    if weather_texts:
        await call.message.edit_text("\n\n".join(weather_texts), parse_mode="Markdown", reply_markup=weather_menu_keyboard())
    else:
        await call.message.edit_text("Немає даних про погоду. Перевірте назви міст!", reply_markup=weather_menu_keyboard())

@router.callback_query(F.data == "weather_5days")
async def callback_weather_5days(call: CallbackQuery):
    user_id = call.from_user.id
    city, _ = get_user_settings(user_id)
    if not city:
        await call.message.edit_text("Спочатку потрібно встановити місто!", reply_markup=main_menu_keyboard())
        return
    # Розбиваємо на кілька міст, якщо введено через кому
    cities = [c.strip() for c in city.split(",") if c.strip()]
    forecast_texts = []
    for c in cities:
        if c:  # Перевіряємо, чи місто не порожнє
            forecast_text = await get_forecast_5days(c)
            forecast_texts.append(forecast_text)
    if forecast_texts:
        await call.message.edit_text("\n\n".join(forecast_texts), parse_mode="Markdown", reply_markup=weather_menu_keyboard())
    else:
        await call.message.edit_text("Немає даних про прогноз. Перевірте назви міст!", reply_markup=weather_menu_keyboard())

@router.message(CityState.waiting_for_city)
async def city_input(message: Message, state: FSMContext):
    cities = [c.strip() for c in message.text.split(",") if c.strip()]
    if not cities:
        await message.answer("Введіть принаймні одне місто (наприклад: Київ, Охтирка, Ужгород).", reply_markup=main_menu_keyboard())
        return
    set_city(message.from_user.id, ", ".join(cities))  # Зберігаємо як список через кому з пробілом
    await message.answer(f"Міста *{', '.join(cities)}* збережено! Тепер можна дізнатися погоду.", reply_markup=main_menu_keyboard())
    await state.clear()

@router.message(NotifyTimeState.waiting_for_times)
async def notify_time_input(message: Message, state: FSMContext):
    times_str = message.text.strip()
    times = [t.strip() for t in times_str.split(",")]
    pattern = r"^([0-1]\d|2[0-3]):([0-5]\d)$"
    for time_str in times:
        if not re.match(pattern, time_str):
            await message.answer("Невірний формат часу. Кожен час має бути у форматі HH:MM (приклад: 15:00, 18:00).")
            return
    set_notify_times(message.from_user.id, times_str)
    user_id = message.from_user.id
    job_id_base = f"user_{user_id}"
    # Видаляємо всі старі завдання для цього користувача
    for job_id in scheduler.get_jobs():
        if job_id.id.startswith(job_id_base):
            scheduler.remove_job(job_id.id)
    # Додаємо нові завдання
    for time_str in times:
        hour, minute = time_str.split(":")
        job_id = f"{job_id_base}_{time_str.replace(':', '_')}"
        scheduler.add_job(
            send_daily_weather,
            trigger='cron',
            hour=int(hour),
            minute=int(minute),
            args=[message.bot, user_id],
            id=job_id,
            replace_existing=True
        )
    await message.answer(f"Сповіщення встановлено на {times_str} щодня!", reply_markup=main_menu_keyboard())
    await state.clear()