import os
from flask import Flask, request
from telethon import TelegramClient, events
import asyncio

# --- Конфигурация ---
API_ID = int(os.getenv("API_ID"))         # из my.telegram.org
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")       # токен бота
SESSION = "bot_session"                  # имя сессии Telethon

WEBHOOK_URL_PATH = "/webhook"            # путь webhook
WEBHOOK_PORT = int(os.getenv("PORT", 10000))  # Render порт

# --- Инициализация Telethon ---
client = TelegramClient(SESSION, API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- Инициализация Flask ---
app = Flask(__name__)

@app.route(WEBHOOK_URL_PATH, methods=["POST"])
def webhook():
    update = request.get_json()
    # Здесь можно обработать update вручную
    print("Получено сообщение:", update)
    return "OK"

# --- Telethon события ---
@client.on(events.NewMessage)
async def handle_new_message(event):
    text = event.message.message
    print("Новое сообщение:", text)
    # Пример: если сообщение содержит ссылку на NFT, переслать себе
    if "t.me/" in text:
        await client.send_message("me", f"Получена ссылка: {text}")

# --- Запуск ---
if __name__ == "__main__":
    # Запуск Telethon в отдельном цикле asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(client.start())
    loop.create_task(client.run_until_disconnected())
    
    # Запуск Flask сервера для webhook
    app.run(host="0.0.0.0", port=WEBHOOK_PORT)
