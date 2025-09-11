import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from db import migrate
from config import BOT_TOKEN

PORT = int(os.environ.get("PORT", 10000))
BOT_URL = os.environ.get("BOT_URL")  # например, https://bs-donate-bot.onrender.com

# ------------------ Хендлеры ------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ------------------ Запуск ------------------
async def main():
    await migrate()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_proof))

    # Здесь запускаем "без управления loop", просто start
    await app.initialize()
    await app.start()
    print("Бот запущен ✅")
    await app.updater.start_polling()  # работает на Render вместо webhook
    await app.updater.idle()  # удерживает процесс

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
