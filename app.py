import asyncio
from typing import Optional
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

from config import BOT_TOKEN, ADMIN_IDS, PAYMENT_TEXT, QIWI_NUMBER, YOOMONEY_WALLET
from db import get_db, migrate

# ---------------- Утилиты ----------------
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

async def set_order_status(order_id: int, status: str, note: Optional[str] = None):
    async with get_db() as db:
        await db.execute(
            "UPDATE orders SET status=?, note=?, updated_at=CURRENT_TIMESTAMP WHERE id=?;",
            (status, note, order_id)
        )

async def get_order(order_id: int):
    async with get_db() as db:
        sql = (
            "SELECT o.id, o.user_id, p.name, o.price, o.status, o.created_at "
            "FROM orders o JOIN products p ON p.id=o.product_id "
            "WHERE o.id=?"
        )
        cur = await db.execute(sql, (order_id,))
        return await cur.fetchone()

async def record_payment(order_id: int, amount: int, proof_file_id: Optional[str]):
    async with get_db() as db:
        await db.execute(
            "INSERT INTO payments (order_id, amount, proof_file_id) VALUES (?, ?, ?);",
            (order_id, amount, proof_file_id)
        )

def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Каталог", callback_data="catalog")],
        [InlineKeyboardButton("📦 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ])

# ---------------- Команды ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_or_create_user(update)
    text = "Добро пожаловать в магазин доната Brawl Stars! Выберите раздел:"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu_kb())
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_kb())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "Нужна помощь? Напишите свой вопрос. Админ ответит.\nТакже используйте /start для меню."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(txt, reply_markup=main_menu_kb())
    else:
        await update.message.reply_text(txt, reply_markup=main_menu_kb())

# ---------------- Каталог ----------------
async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await list_active_products()
    if not rows:
        txt = "Каталог пуст. Обратитесь к администратору."
        if update.callback_query:
            await update.callback_query.edit_message_text(txt, reply_markup=main_menu_kb())
        else:
            await update.message.reply_text(txt, reply_markup=main_menu_kb())
        return
    keyboard = [[InlineKeyboardButton(f"{name} — {price}₽", callback_data=f"prod_{pid}")] for pid, name, price, _ in rows]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_main")])
    kb = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text("Выберите товар:", reply_markup=kb)
    else:
        await update.message.reply_text("Выберите товар:", reply_markup=kb)

async def product_view(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int):
    async with get_db() as db:
        cur = await db.execute("SELECT id, name, price, description FROM products WHERE id=?;", (product_id,))
        row = await cur.fetchone()
    if not row:
        await update.callback_query.answer("Товар не найден", show_alert=True)
        return
    pid, name, price, description = row
    text = f"*{name}* — *{price}₽*\n\n{description or ''}\n\nНажмите «Купить», чтобы оформить заказ."
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Купить", callback_data=f"buy_{pid}")],
        [InlineKeyboardButton("⬅️ Каталог", callback_data="catalog")]
    ])
    await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

# ---------------- Main ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # кнопки
    app.add_handler(CallbackQueryHandler(catalog, pattern="^catalog$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: product_view(u, c, int(u.callback_query.data.split("_")[1])), pattern="^prod_"))

    # запуск
    app.run_polling()

if __name__ == "__main__":
    asyncio.run(migrate())
    main()
