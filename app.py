import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN, ADMIN_IDS, PAYMENT_TEXT, QIWI_NUMBER, YOOMONEY_WALLET
from db import get_db, migrate

# ----------------------- Утилиты -----------------------
async def get_or_create_user(update: Update):
    u = update.effective_user
    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?);",
            (u.id, u.username, u.first_name)
        )

def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Каталог", callback_data="catalog")],
        [InlineKeyboardButton("📦 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ])

# ----------------------- Хендлеры -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_or_create_user(update)
    if update.message:
        await update.message.reply_text(
            "Привет! Я донат-бот для Brawl Stars!",
            reply_markup=main_menu_kb()
        )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Нужна помощь? Напишите сюда свой вопрос.\n"
            "Администратор увидит ваше сообщение.\n\n"
            "Также используйте /start для меню.",
            reply_markup=main_menu_kb()
        )

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = None
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        return
    await update.message.reply_text("Спасибо! Чек получен. Админ проверит оплату.")

# ----------------------- Основной запуск -----------------------
PORT = int(os.environ.get("PORT", 10000))
BOT_URL = os.environ.get("BOT_URL")  # https://bs-donate-bot.onrender.com
webhook_path = f"/{BOT_TOKEN}"

async def main():
    await migrate()  # Миграция базы

    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем хендлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_proof))

    print("Бот запущен ✅")

    # Запуск вебхука
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{BOT_URL}{webhook_path}"
    )

# ----------------------- Старт -----------------------
if __name__ == "__main__":
    import asyncio
    import sys

    # Render сам запускает loop, поэтому просто делаем так:
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
    except RuntimeError:
        # Если loop уже запущен, создаем задачу и не закрываем loop
        asyncio.ensure_future(main())
