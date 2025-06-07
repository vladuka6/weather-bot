import os
BOT_TOKEN = os.getenv("BOT_TOKEN", "7988184310:AAFEU86dvc5_dOJdLrrB9QDTcm_O1bTWGLU")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://weather-bot-vqyf.onrender.com/webhook")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "e0904bca4dfb0fcd415d4a0bc2509201")
OPENWEATHER_BASE_URL = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5/")
DB_NAME = "weather_bot.db"