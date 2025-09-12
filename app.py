import os
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
    await update.message.reply_text("Привет! Я донат-бот для Brawl Stars!", reply_markup=main_menu_kb())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Нужна помощь? Напиши сюда свой вопрос. Админ увидит сообщение.\n\n"
        "Также используйте /start для меню.",
        reply_markup=main_menu_kb()
    )

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Спасибо! Чек получен. Админ проверит оплату.")

# ---------------------- Главная функция ----------------------
def main():
    asyncio.run(migrate())  # база мигрируется один раз

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_proof))

    print("Бот запущен ✅")

    # 🛠 ФИКС: явно создаём event loop для PTB (Python 3.13 требует)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{BOT_URL}{WEBHOOK_PATH}"
    )

if __name__ == "__main__":
    main()
