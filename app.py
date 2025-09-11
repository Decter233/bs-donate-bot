import asyncio
from typing import Optional
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

from config import BOT_TOKEN, ADMIN_IDS, PAYMENT_TEXT, QIWI_NUMBER, YOOMONEY_WALLET
from db import get_db, migrate


# ----------------------- Утилиты -----------------------
def order_code(order_id: int) -> str:
    return f"ORDER-{order_id:06d}"


async def get_or_create_user(update: Update):
    u = update.effective_user
    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?);",
            (u.id, u.username, u.first_name)
        )


async def list_active_products():
    async with get_db() as db:
        cur = await db.execute("SELECT id, name, price, description FROM products WHERE is_active=1 ORDER BY id;")
        return await cur.fetchall()


async def create_order(user_id: int, product_id: int, price: int) -> int:
    async with get_db() as db:
        cur = await db.execute(
            "INSERT INTO orders (user_id, product_id, price, status) VALUES (?, ?, ?, 'awaiting_payment');",
            (user_id, product_id, price)
        )
        return cur.lastrowid


# ----------------------- Клавиатура -----------------------
def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Каталог", callback_data="catalog")],
        [InlineKeyboardButton("📦 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ])


# ----------------------- Команды -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_or_create_user(update)
    await update.message.reply_text(
        "Добро пожаловать в магазин доната Brawl Stars!",
        reply_markup=main_menu_kb()
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Нужна помощь? Напишите сюда свой вопрос.\n"
        "Администратор увидит ваше сообщение.\n\n"
        "Также используйте /start для меню.",
        reply_markup=main_menu_kb()
    )


# ----------------------- Обработка фото/доков -----------------------
async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = None
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        return

    await update.message.reply_text("Спасибо! Чек получен. Админ проверит оплату.")


# ----------------------- Главная функция -----------------------
async def main():
    # миграция базы
    await migrate()

    # создаём приложение
    app = Application.builder().token(BOT_TOKEN).build()

    # хендлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_proof))

    print("Бот запущен ✅")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
