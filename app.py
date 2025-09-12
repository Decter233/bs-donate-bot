import os
import asyncio
from aiohttp import web
from telegram.ext import Application, CommandHandler

# --- Настройки ---
TOKEN = os.getenv("BOT_TOKEN")
BOT_URL = os.getenv("BOT_URL", "https://bs-donate-bot.onrender.com")
WEBHOOK_PATH = f"/{TOKEN}"
PORT = int(os.getenv("PORT", 10000))

# --- Создание бота ---
app = Application.builder().token(TOKEN).build()

async def start(update, context):
    await update.message.reply_text("Привет! Бот работает ✅")

app.add_handler(CommandHandler("start", start))

# HTTP проверка
async def handle_root(request):
    return web.Response(text="Бот жив ✅", content_type="text/plain")

async def init():
    webhook_url = f"{BOT_URL}{WEBHOOK_PATH}"
    print(f"Устанавливаю вебхук: {webhook_url}")
    await app.bot.set_webhook(webhook_url)

    aio_app = web.Application()
    aio_app.router.add_get("/", handle_root)
    runner = web.AppRunner(aio_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # вместо await → запускаем как фоновую задачу
    asyncio.create_task(
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=webhook_url,
            drop_pending_updates=True
        )
    )

# запуск через существующий loop
loop = asyncio.get_event_loop()
loop.create_task(init())
loop.run_forever()
