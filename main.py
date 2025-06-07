import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
import aiohttp.web

from database import init_db
from config import BOT_TOKEN, WEBHOOK_URL
from handlers import router
from scheduler import schedule_jobs, start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

init_db()

async def on_startup(app):
    logger.info("Бот запущено!")
    await bot.set_webhook(url=WEBHOOK_URL)
    start_scheduler()
    await schedule_jobs(bot)

async def on_shutdown(app):
    logger.info("Бот зупинено!")
    await bot.delete_webhook()
    await dp.storage.close()
    await bot.session.close()

async def start_webhook():
    app = aiohttp.web.Application()
    async def handle(request):
        if request.method == "POST":
            try:
                logger.info("Received webhook request")
                update = Update(**await request.json())
                await dp.feed_update(bot=bot, update=update)
                return aiohttp.web.Response(text="OK")
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                return aiohttp.web.Response(status=500)
        return aiohttp.web.Response(status=404)

    app.router.add_post("/webhook", handle)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, host="0.0.0.0", port=10000)
    await site.start()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await asyncio.Future()
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(start_webhook())