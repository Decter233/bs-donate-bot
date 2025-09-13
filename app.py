import os
import asyncio
from telegram.ext import Application, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")
BOT_URL = os.getenv("BOT_URL", "https://bs-donate-bot.onrender.com")
WEBHOOK_PATH = f"/{TOKEN}"
PORT = int(os.getenv("PORT", 10000))

app = Application.builder().token(TOKEN).build()

async def start(update, context):
    user = update.effective_user
    print(f"Кто-то написал /start: {user.id} ({user.username})")
    await update.message.reply_text("Привет! Бот работает ✅")

app.add_handler(CommandHandler("start", start))

async def init():
    webhook_url = f"{BOT_URL}{WEBHOOK_PATH}"
    print(f"Устанавливаю вебхук: {webhook_url}")

    await app.bot.set_webhook(webhook_url)

    await app.initialize()
    await app.start()
    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=webhook_url,
        drop_pending_updates=True
    )

loop = asyncio.get_event_loop()
loop.create_task(init())
loop.run_forever()
