import os
from aiohttp import web
from telegram.ext import Application, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")
BOT_URL = os.getenv("BOT_URL", "https://bs-donate-bot.onrender.com")
WEBHOOK_PATH = f"/{TOKEN}"
PORT = int(os.getenv("PORT", 10000))

app = Application.builder().token(TOKEN).build()

# --- Команды бота ---
async def start(update, context):
    await update.message.reply_text("Привет! Бот работает ✅")

app.add_handler(CommandHandler("start", start))

# --- HTTP ручка для проверки ---
async def handle_root(request):
    return web.Response(text="Бот жив ✅", content_type="text/plain")

async def init():
    # 1) Устанавливаем вебхук
    webhook_url = f"{BOT_URL}{WEBHOOK_PATH}"
    print(f"Устанавливаю вебхук: {webhook_url}")
    await app.bot.set_webhook(webhook_url)

    # 2) Поднимаем aiohttp-сервер
    aio_app = web.Application()
    aio_app.router.add_get("/", handle_root)
    runner = web.AppRunner(aio_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # 3) Запускаем приложение Telegram (webhook)
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=webhook_url,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init())
