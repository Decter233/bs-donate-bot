import os
import asyncio
from telegram.ext import Application, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")
BOT_URL = os.getenv("BOT_URL", "https://bs-donate-bot.onrender.com")
WEBHOOK_PATH = f"/{TOKEN}"
PORT = int(os.getenv("PORT", 10000))

app = Application.builder().token(TOKEN).build()

async def start(update, context):
    print(f"Пришёл /start от {update.effective_user.username} ({update.effective_user.id})")
    await update.message.reply_text("Привет! Бот на вебхуке работает ✅")

async def main():
    webhook_url = f"{BOT_URL}{WEBHOOK_PATH}"
    print(f"Устанавливаю вебхук: {webhook_url}")
    await app.bot.set_webhook(webhook_url, drop_pending_updates=True)
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=webhook_url,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    asyncio.run(main())
