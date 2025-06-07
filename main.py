import logging
import asyncio
from aiogram.client.bot import Bot, DefaultBotProperties
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from database import init_db
from config import BOT_TOKEN
from handlers import router
from scheduler import schedule_jobs, start_scheduler

logging.basicConfig(level=logging.INFO)


async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    start_scheduler()
    schedule_jobs(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
