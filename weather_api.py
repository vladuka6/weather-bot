import aiohttp
from config import OPENWEATHER_API_KEY, OPENWEATHER_BASE_URL
from collections import defaultdict
from datetime import datetime

async def get_current_weather(city: str, lang: str = "uk") -> str:
    """Запитує поточну погоду в місті."""
    url = f"{OPENWEATHER_BASE_URL}/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": lang
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                data = await response.json()
                if response.status != 200:
                    return f"⚠️ Помилка: {data.get('message', 'Не вдалося отримати погоду. Перевірте ключ API або назву міста.')}"
                weather_desc = data["weather"][0]["description"].capitalize()
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                wind_speed = data["wind"]["speed"]

                # Додаємо емодзі залежно від погоди
                weather_emoji = "☀️" if "чисте небо" in weather_desc.lower() else "☁️" if "хмари" in weather_desc.lower() else "🌦️" if "дощ" in weather_desc.lower() else "⛅"
                temp_emoji = "🔥" if temp > 28 else "🌞" if temp > 24 else "😎"
                feels_emoji = "🥵" if feels_like > 28 else "😓" if feels_like > 24 else "😊"
                humidity_emoji = "🌧️" if humidity > 60 else "💦"
                wind_emoji = "🌬️" if wind_speed > 5 else "🍃"

                # Формуємо текст із емодзі
                weather_text = (
                    f"🌤 **Погода в місті *{city.title()}* 🌆**:\n\n"
                    f"{weather_emoji} • **{weather_desc}**\n"
                    f"🌡️ • **Температура**: {temp}°C {temp_emoji}\n"
                    f"{feels_emoji} • **Відчувається як**: {feels_like}°C\n"
                    f"💧 • **Вологість**: {humidity}% {humidity_emoji}\n"
                    f"💨 • **Вітер**: {wind_speed} м/с {wind_emoji}\n"
                )

                # Додаємо цікавий висновок
                if temp > 28:
                    conclusion = f"**Висновок**: Спекотний день у {city.title()}! 🔥 Час для прохолодних напоїв 🥤 і легкого одягу 👕. Не забудь сонцезахисний крем! 🧴"
                elif temp > 24:
                    conclusion = f"**Висновок**: Тепло і приємно у {city.title()}! 🌞 Ідеально для прогулянки парком 🌳 чи пікніка 🍉."
                else:
                    conclusion = f"**Висновок**: Комфортна погода у {city.title()}! 😎 Чудовий день для активного відпочинку 🚴‍♀️ чи затишного чаювання ☕."

                if humidity > 60:
                    conclusion += " Але вологість висока, тож бери парасольку на всяк випадок! ☂️"

                return weather_text + "\n" + conclusion
    except aiohttp.ClientError as e:
        return f"⚠️ Помилка підключення до сервісу погоди: {str(e)}"

async def get_forecast_5days(city: str, lang: str = "uk") -> str:
    """Запитує 5-денний прогноз погоди і групує дані за днями."""
    url = f"{OPENWEATHER_BASE_URL}/forecast"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": lang
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                data = await response.json()
                if response.status != 200:
                    return f"⚠️ Помилка: {data.get('message', 'Не вдалося отримати прогноз. Перевірте ключ API або назву міста.')}"
                forecast_list = data.get("list", [])
                if not forecast_list:
                    return "⚠️ Немає даних прогнозу."

                grouped = defaultdict(list)
                for entry in forecast_list:
                    date = entry["dt_txt"].split(" ")[0]
                    grouped[date].append(entry)

                days = sorted(grouped.keys())
                lines = [f"📅 **Прогноз погоди на 5 днів у *{city.title()}* 🌟**:\n"]
                avg_temps = []
                rainy_days = 0
                for day in days[:5]:
                    entries = grouped[day]
                    chosen = next((entry for entry in entries if "12:00:00" in entry["dt_txt"]), entries[0])
                    dt_obj = datetime.strptime(day, "%Y-%m-%d")
                    formatted_date = dt_obj.strftime("%d.%m.%Y")
                    desc = chosen["weather"][0]["description"].capitalize()
                    temp = chosen["main"]["temp"]
                    temp_min = chosen["main"]["temp_min"]
                    temp_max = chosen["main"]["temp_max"]
                    wind_speed = chosen["wind"]["speed"]
                    humidity = chosen["main"]["humidity"]

                    # Додаємо емодзі для прогнозу
                    weather_emoji = "☀️" if "чисте небо" in desc.lower() else "☁️" if "хмари" in desc.lower() else "🌦️" if "дощ" in desc.lower() else "⛅"
                    temp_emoji = "🔥" if temp > 28 else "🌞" if temp > 24 else "😎"
                    humidity_emoji = "🌧️" if humidity > 60 else "💦"
                    wind_emoji = "🌬️" if wind_speed > 5 else "🍃"

                    lines.append(
                        f"📍 **{formatted_date}** 🗓️\n"
                        f"{weather_emoji} • **{desc}**\n"
                        f"🌡️ • **Температура**: {temp}°C (мін: {temp_min}°C, макс: {temp_max}°C) {temp_emoji}\n"
                        f"💧 • **Вологість**: {humidity}% {humidity_emoji}\n"
                        f"💨 • **Вітер**: {wind_speed} м/с {wind_emoji}\n"
                    )
                    avg_temps.append(temp)
                    if "дощ" in desc.lower():
                        rainy_days += 1

                # Додаємо цікавий висновок для прогнозу
                avg_temp = sum(avg_temps) / len(avg_temps)
                if avg_temp > 28:
                    conclusion = f"**Висновок для {city.title()}**: Спекотний тиждень попереду! 🔥 Чудовий час для пікніків 🍉 і відпочинку на природі 🌳."
                elif avg_temp > 24:
                    conclusion = f"**Висновок для {city.title()}**: Теплий і приємний тиждень! 🌞 Ідеально для прогулянок 🚶‍♀️ і активного відпочинку 🚴‍♀️."
                else:
                    conclusion = f"**Висновок для {city.title()}**: Комфортна погода на весь тиждень! 😎 Час для затишних вечорів ☕ і легких прогулянок 🌄."

                if rainy_days > 0:
                    conclusion += f" Але чекай на {rainy_days} дощових днів 🌧️, тож тримай парасольку напоготові! ☂️"
                else:
                    conclusion += " Сонячна погода гарантована, бери сонцезахисний крем! 🧴"

                return "\n".join(lines) + "\n" + conclusion
    except aiohttp.ClientError as e:
        return f"⚠️ Помилка підключення до сервісу прогнозу погоди: {str(e)}"