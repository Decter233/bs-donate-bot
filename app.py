import os
import nest_asyncio
import asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from db import migrate
from config import BOT_TOKEN

# ---------------------- Настройки Render ----------------------
PORT = int(os.environ.get("PORT", 10000))
BOT_URL = os.environ.get("BOT_URL")  # Пример: https://bs-donate-bot.onrender.com
WEBHOOK_PATH = f"/{BOT_TOKEN}"

# ---------------------- Клавиатура ----------------------
def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Каталог", callback_data="catalog")],
        [InlineKeyboardButton("📦 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ])

# ---------------------- Хендлеры ----------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я донат-бот для Brawl Stars!",
        reply_markup=main_menu_kb()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Нужна помощь? Напиши сюда свой вопрос. Админ увидит сообщение.\n\n"
        "Также используйте /start для меню.",
        reply_markup=main_menu_kb()
    )

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Спасибо! Чек получен. Админ проверит оплату.")

# ---------------------- Главная функция ----------------------
async def main():
    # Миграция базы
    await migrate()

    # Создаём приложение бота
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем хендлеры
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_proof))

    print("Бот запущен ✅")

    # Запуск webhook
    await app.run_webhook(
        listen="0.0.0.0",            # обязательно для Render
        port=PORT,                   # порт из Render
        webhook_url=f"{BOT_URL}{WEBHOOK_PATH}"  # публичный URL + токен
    )

# ---------------------- Старт ----------------------
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
