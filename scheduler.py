from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_all_users, get_user_settings
from weather_api import get_current_weather
from aiogram import Bot
import pytz

# Ініціалізація планувальника з часовим поясом
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Kyiv"))

async def send_daily_weather(bot: Bot, user_id: int):
    """Надсилає щоденне сповіщення з погодою."""
    city, _ = get_user_settings(user_id)
    if not city:
        return
    weather_text = await get_current_weather(city)
    try:
        await bot.send_message(chat_id=user_id, text=weather_text, parse_mode="Markdown")
    except Exception:
        pass

def schedule_jobs(bot: Bot):
    """Додає завдання для всіх користувачів із встановленим notify_times."""
    users = get_all_users()
    for user_id, city, notify_times in users:
        if notify_times:
            job_id_base = f"user_{user_id}"
            # Видаляємо всі старі завдання для цього користувача
            for job_id in scheduler.get_jobs():
                if job_id.id.startswith(job_id_base):
                    scheduler.remove_job(job_id.id)
            # Додаємо нові завдання для кожного часу
            times = [t.strip() for t in notify_times.split(",")]
            for time_str in times:
                hour, minute = time_str.split(":")
                job_id = f"{job_id_base}_{time_str.replace(':', '_')}"
                scheduler.add_job(
                    send_daily_weather,
                    trigger='cron',
                    hour=int(hour),
                    minute=int(minute),
                    args=[bot, user_id],
                    id=job_id,
                    replace_existing=True
                )

def start_scheduler():
    scheduler.start()