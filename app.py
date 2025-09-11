import os
import nest_asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from config import BOT_TOKEN, ADMIN_IDS
from db import get_db, migrate

# ----------------------- Настройка вебхука -----------------------
PORT = int(os.environ.get("PORT", 8443))
URL = os.environ.get("URL")  # например "https://bs-donate-bot.onrender.com"

nest_asyncio.apply()  # исправляет "event loop is already running"

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
        "Привет! Я донат-бот для Brawl Stars!",
        reply_markup=main_menu_kb()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Нужна помощь? Напишите сюда свой вопрос.\nАдмин увидит ваше сообщение.",
        reply_markup=main_menu_kb()
    )

# ----------------------- Обработчики кнопок -----------------------
async def catalog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    products = await list_active_products()
    text = "\n".join([f"{p[1]} - {p[2]}₽\n{p[3]}" for p in products]) or "Нет доступных продуктов"
    await update.callback_query.message.edit_text(text, reply_markup=main_menu_kb())

async def my_orders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Здесь будут ваши заказы", reply_markup=main_menu_kb())

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Напишите свой вопрос, админ ответит",
        reply_markup=main_menu_kb()
    )

# ----------------------- Фото/документы -----------------------
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
    await migrate()  # миграция БД

    app = Application.builder().token(BOT_TOKEN).build()

    # Хендлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    app.add_handler(CallbackQueryHandler(catalog_handler, pattern="catalog"))
    app.add_handler(CallbackQueryHandler(my_orders_handler, pattern="my_orders"))
    app.add_handler(CallbackQueryHandler(help_handler, pattern="help"))

    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_proof))

    print("Бот запущен ✅")

    # Запуск вебхука
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{URL}/{BOT_TOKEN}"
    )

# ----------------------- Запуск -----------------------
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
