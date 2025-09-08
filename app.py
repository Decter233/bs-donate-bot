import asyncio
from typing import Optional

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

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

# ----------------------- Команды -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_or_create_user(update)
    text = "Добро пожаловать в магазин доната Brawl Stars! Выберите раздел:"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu_kb())
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_kb())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "Нужна помощь? Напишите сюда свой вопрос. Администратор увидит ваше сообщение.\nТакже используйте /start для меню."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(txt, reply_markup=main_menu_kb())
    else:
        await update.message.reply_text(txt, reply_markup=main_menu_kb())

# ----------------------- Каталог и заказы -----------------------
async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await list_active_products()
    if not rows:
        txt = "Каталог пуст. Обратитесь к администратору."
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(txt, reply_markup=main_menu_kb())
        else:
            await update.message.reply_text(txt, reply_markup=main_menu_kb())
        return
    keyboard = [[InlineKeyboardButton(f"{name} — {price}₽", callback_data=f"prod_{pid}")] for pid, name, price, _ in rows]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_main")])
    kb = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.answer()
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

async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int):
    async with get_db() as db:
        cur = await db.execute("SELECT id, name, price FROM products WHERE id=?;", (product_id,))
        row = await cur.fetchone()
    if not row:
        await update.callback_query.answer("Товар не найден", show_alert=True)
        return
    pid, name, price = row
    order_id = await create_order(update.effective_user.id, pid, price)
    oc = order_code(order_id)
    pay_lines = []
    if YOOMONEY_WALLET:
        pay_lines.append(f"ЮMoney: `{YOOMONEY_WALLET}`")
    if QIWI_NUMBER:
        pay_lines.append(f"QIWI: `{QIWI_NUMBER}`")
    pay_info = "\n".join(pay_lines) if pay_lines else "ЮMoney / QIWI реквизиты уточняйте у администратора."
    text = (
        f"✅ Заказ создан: *{name}* за *{price}₽*.\n"
        f"Номер заказа: *{oc}*\n\n"
        f"{PAYMENT_TEXT.format(order_code=oc)}\n\n"
        f"{pay_info}\n\n"
        f"После оплаты отправьте *скриншот* в этот чат или нажмите «Я оплатил(а)»."
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Я оплатил(а)", callback_data=f"paid_{order_id}")],
        [InlineKeyboardButton("⬅️ В меню", callback_data="back_main")]
    ])
    await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"🆕 Новый заказ {oc}\nПокупатель: {update.effective_user.mention_html()}\nТовар: {name}\nСумма: {price}₽",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отметить оплачено", callback_data=f"admin_mark_paid_{order_id}"),
                                                   InlineKeyboardButton("Отклонить", callback_data=f"admin_reject_{order_id}")]])
            )
        except Exception:
            pass

# ----------------------- Main -----------------------
async def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is not set")

    await migrate()  # миграция БД перед запуском

    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрация хендлеров
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_menu))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_proof))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    # Запуск бота
    await app.run_polling()  # run_polling в PTB 20+ сам блокирует цикл

if __name__ == "__main__":
    asyncio.run(main())
