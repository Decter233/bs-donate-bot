import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from db import get_db, migrate
from config import BOT_TOKEN

# ------------------ Хендлеры ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я донат-бот для Brawl Stars!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Каталог", callback_data="catalog")],
            [InlineKeyboardButton("📦 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ])
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используйте /start для меню.")

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Спасибо! Чек получен. Админ проверит оплату.")

# ------------------ Основной запуск ------------------
PORT = int(os.environ.get("PORT", 10000))
BOT_URL = os.environ.get("BOT_URL")  # Render URL

async def main():
    await migrate()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_proof))

    print("Бот запущен ✅")

    # Запуск вебхука без asyncio.run()
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{BOT_URL}/{BOT_TOKEN}"
    )

# ------------------ Запуск ------------------
if __name__ == "__main__":
    import asyncio

    # Render уже имеет running loop, создаём задачу
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.create_task(main())
    loop.run_forever()
