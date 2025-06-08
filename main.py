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
logger.info("Dispatcher and router initialized")

init_db()

async def on_startup(app):
    logger.info("Бот запущено!")
    await bot.set_webhook(url=WEBHOOK_URL)
    start_scheduler()
    await schedule_jobs(bot)
    logger.info("Webhook set and scheduler started")

async def on_shutdown(app):
    logger.info("Бот зупинено!")
    await bot.delete_webhook()
    await dp.storage.close()
    await bot.session.close()

async def start_webhook():
    app = aiohttp.web.Application()

    async def handle_root(request):
        return aiohttp.web.Response(text="Бот працює")

    async def handle_webhook(request):
        if request.method == "POST":
            try:
                logger.info("Отримано запит до webhook")
                data = await request.json()
                logger.info(f"Дані webhook: {data}")
                if not isinstance(data, dict) or 'update_id' not in data:
                    logger.error("Невірний формат даних webhook")
                    return aiohttp.web.Response(status=400)
                update = Update(**data)
                logger.info("Передача оновлення до диспетчера")
                await dp.feed_update(bot=bot, update=update)
                logger.info("Оновлення оброблено успішно")
                return aiohttp.web.Response(text="OK")
            except Exception as e:
                logger.error(f"Помилка обробки webhook: {e}", exc_info=True)
                return aiohttp.web.Response(status=500)
        return aiohttp.web.Response(status=404)

    app.router.add_get("/", handle_root)
    app.router.add_post("/webhook", handle_webhook)
    
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, host="0.0.0.0", port=10000)
    await site.start()
    logger.info("Сервер запущено на 0.0.0.0:10000")

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await asyncio.Future()
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(start_webhook())