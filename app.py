import os
import asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from config import BOT_TOKEN
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
        cur = await db.execute(
            "SELECT id, name, price, description FROM products WHERE is_active=1 ORDER BY id;"
        )
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

def back_to_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu")]
    ])

def product_kb(product_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Купить", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="catalog")]
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

# ----------------------- Обработка CallbackQuery -----------------------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "main_menu":
        await query.edit_message_text("Главное меню:", reply_markup=main_menu_kb())
    
    elif query.data == "catalog":
        products = await list_active_products()
        if not products:
            await query.edit_message_text("Каталог пуст.", reply_markup=back_to_menu_kb())
            return
        # показываем первый продукт
        product = products[0]
        text = f"{product['name']} — {product['price']}₽\n{product['description']}"
        await query.edit_message_text(
            text,
            reply_markup=product_kb(product['id'])
        )
        # сохраняем список продуктов и индекс в context
        context.user_data["products"] = products
        context.user_data["index"] = 0

    elif query.data.startswith("buy_"):
        product_id = int(query.data.split("_")[1])
        user_id = query.from_user.id
        products = await list_active_products()
        product = next((p for p in products if p["id"] == product_id), None)
        if product:
            order_id = await create_order(user_id, product_id, product["price"])
            await query.edit_message_text(
                f"Заказ создан! Ваш код заказа: {order_code(order_id)}\n"
                f"Оплатите и отправьте чек в чат.",
                reply_markup=main_menu_kb()
            )
        else:
            await query.edit_message_text("Товар не найден.", reply_markup=back_to_menu_kb())

    elif query.data == "my_orders":
        await query.edit_message_text("Ваши заказы пока недоступны.", reply_markup=back_to_menu_kb())

    elif query.data == "help":
        await query.edit_message_text(
            "Нужна помощь? Напишите сюда свой вопрос.\nАдмин увидит ваше сообщение.",
            reply_markup=back_to_menu_kb()
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
    await migrate()

    app = Application.builder().token(BOT_TOKEN).build()

    # Хендлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_proof))
    app.add_handler(CallbackQueryHandler(menu_handler))

    # Webhook для Render
    PORT = int(os.environ.get("PORT", 8443))
    URL = os.environ.get("RENDER_EXTERNAL_URL", "//https://bs-donate-bot.onrender.com")
    webhook_path = f"/{BOT_TOKEN}"

    print("Бот запущен ✅")
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{URL}{webhook_path}"
    )

# ----------------------- Точка входа -----------------------
if __name__ == "__main__":
    asyncio.run(main())
