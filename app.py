import os
import asyncio
from aiohttp import web
from telegram.ext import Application, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")
BOT_URL = os.getenv("BOT_URL", "https://bs-donate-bot.onrender.com")
WEBHOOK_PATH = f"/{TOKEN}"
PORT = int(os.getenv("PORT", 10000))

app = Application.builder().token(TOKEN).build()

async def start(update, context):
    await update.message.reply_text("Привет! Бот работает ✅")

app.add_handler(CommandHandler("start", start))

# --- HTTP сервер для Render ---
async def handle_root(request):
    return web.Response(text="Бот жив ✅", content_type="text/plain")

async def run():
    webhook_url = f"{BOT_URL}{WEBHOOK_PATH}"
    print(f"Устанавливаю вебхук: {webhook_url}")
    await app.bot.set_webhook(webhook_url)

    runner = web.AppRunner(web.Application())
    runner.app.router.add_get("/", handle_root)

    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=webhook_url,
    )

if __name__ == "__main__":
    asyncio.run(run())
