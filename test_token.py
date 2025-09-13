import os
import requests

token = os.getenv("BOT_TOKEN")

if not token:
    print("❌ Переменная BOT_TOKEN не найдена! Проверь настройки Render.")
    exit(1)

print(f"✅ BOT_TOKEN найден: {token[:10]}...")

url = f"https://api.telegram.org/bot{token}/getMe"
response = requests.get(url)

print("📡 Ответ Telegram API:")
print(response.text)

if response.status_code == 200:
    print("✅ Токен рабочий, можно запускать бота.")
else:
    print("❌ Токен невалидный или бот удалён. Проверь в BotFather!")
