import os
import nest_asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from db import migrate
from config import BOT_TOKEN

# ---------------------- Настройки Render ----------------------
PORT = int(os.environ.get("PORT", 10000))
BOT_URL = os.environ.get("BOT_URL")  # https://bs-donate-bot.onrender.com
WEBHOOK_PATH = f"/{BOT_TOKEN}"

# ---------------------- Хендлеры ----------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я донат-бот для Brawl Stars!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Каталог", callback_data="catalog")]])
    )

# ---------------------- Главная функция ----------------------
async def main():
    # Миграция базы
    await migrate()

    # Создаём приложение бота
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем хендлеры
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, lambda u, c: u.message.reply_text("Чек получен!")))

    # Запуск webhook
    await app.run_webhook(
        listen="0.0.0.0",           # обязательно для Render
        port=PORT,                  # порт из Render
        webhook_url=f"{BOT_URL}{WEBHOOK_PATH}"  # публичный URL + токен
    )

# ---------------------- Старт ----------------------
if __name__ == "__main__":
    import asyncio
    nest_asyncio.apply()  # предотвращает ошибки loop
    asyncio.run(main())
