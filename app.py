import asyncio
from typing import Optional

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

from config import BOT_TOKEN, ADMIN_IDS, PAYMENT_TEXT, QIWI_NUMBER, YOOMONEY_WALLET
from db import get_db, migrate

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
        rows = await cur.fetchall()
        return rows

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_or_create_user(update)
    text = "Добро пожаловать в магазин доната Brawl Stars! Выберите раздел:"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu_kb())
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_kb())

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
    keyboard = []
    for pid, name, price, _ in rows:
        keyboard.append([InlineKeyboardButton(f"{name} — {price}₽", callback_data=f"prod_{pid}")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_main")])
    kb = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        q = update.callback_query
        await q.answer()
        await q.edit_message_text("Выберите товар:", reply_markup=kb)
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

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with get_db() as db:
        sql = (
            "SELECT o.id, p.name, o.price, o.status, o.created_at "
            "FROM orders o JOIN products p ON p.id=o.product_id "
            "WHERE o.user_id=? ORDER BY o.id DESC LIMIT 10;"
        )
        cur = await db.execute(sql, (update.effective_user.id,))
        rows = await cur.fetchall()
    if not rows:
        txt = "Пока заказов нет."
    else:
        lines = []
        for oid, name, price, status, created in rows:
            lines.append(f"{order_code(oid)} — {name} — {price}₽ — {status}")
        txt = "Ваши последние заказы:\n" + "\n".join(lines)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(txt, reply_markup=main_menu_kb())
    else:
        await update.message.reply_text(txt, reply_markup=main_menu_kb())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "Нужна помощь? Напишите сюда свой вопрос. Администратор увидит ваше сообщение.\nТакже используйте /start для меню."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(txt, reply_markup=main_menu_kb())
    else:
        await update.message.reply_text(txt, reply_markup=main_menu_kb())

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    file_id = None
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        return
    async with get_db() as db:
        cur = await db.execute(
            "SELECT id, price FROM orders WHERE user_id=? AND status='awaiting_payment' ORDER BY id DESC LIMIT 1;",
            (u.id,)
        )
        row = await cur.fetchone()
    if not row:
        await update.message.reply_text("Не нашёл активного заказа в статусе ожидания оплаты. Оформите заказ из каталога.")
        return
    order_id, price = row
    await record_payment(order_id, amount=price, proof_file_id=file_id)
    oc = order_code(order_id)
    await update.message.reply_text(f"Спасибо! Чек для {oc} получен. Ожидайте подтверждения администратором.")
    for admin_id in ADMIN_IDS:
        try:
            if update.message.photo:
                await context.bot.send_photo(admin_id, file_id, caption=f"🧾 Чек по {oc} от @{u.username or u.id}")
            elif update.message.document:
                await context.bot.send_document(admin_id, file_id, caption=f"🧾 Чек по {oc} от @{u.username or u.id}")
            await context.bot.send_message(admin_id, f"Проверить заказ {oc}?",
                                           reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отметить оплачено", callback_data=f"admin_mark_paid_{order_id}"),
                                                                               InlineKeyboardButton("Отклонить", callback_data=f"admin_reject_{order_id}")]]))
        except Exception:
            pass

def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        uid = update.effective_user.id
        if uid not in ADMIN_IDS:
            if update.callback_query:
                await update.callback_query.answer("Недостаточно прав", show_alert=True)
            else:
                await update.message.reply_text("Недостаточно прав.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

@admin_only
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧾 Заказы (ожидают)", callback_data="admin_orders_pending")],
        [InlineKeyboardButton("➕ Товары (добавить)", callback_data="admin_add_product")],
        [InlineKeyboardButton("📦 Товары (список)", callback_data="admin_list_products")]
    ])
    if update.message:
        await update.message.reply_text("Админ-меню:", reply_markup=kb)
    else:
        await update.callback_query.edit_message_text("Админ-меню:", reply_markup=kb)

@admin_only
async def admin_orders_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with get_db() as db:
        sql = ("SELECT o.id, p.name, o.price, o.created_at, u.username FROM orders o JOIN products p ON p.id=o.product_id JOIN users u ON u.user_id=o.user_id WHERE o.status='awaiting_payment' ORDER BY o.id ASC LIMIT 20;")
        cur = await db.execute(sql)
        rows = await cur.fetchall()
    if not rows:
        txt = "Ожидающих заказов нет."
    else:
        lines = []
        for oid, pname, price, created, username in rows:
            lines.append(f"{order_code(oid)} — {pname} — {price}₽ — @{username or 'user'}")
        txt = "Ожидают оплаты:\n" + "\n".join(lines)
    await update.callback_query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]]))

@admin_only
async def admin_mark_paid(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int):
    await set_order_status(order_id, "paid")
    oc = order_code(order_id)
    await update.callback_query.answer(f"{oc} отмечен как оплаченный", show_alert=True)
    order = await get_order(order_id)
    if order:
        _, user_id, pname, price, status, _ = order
        try:
            await context.bot.send_message(user_id, f"Ваш заказ {oc} подтверждён как оплаченный. Ожидайте начисления доната.")
        except Exception:
            pass

@admin_only
async def admin_reject(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int):
    await set_order_status(order_id, "rejected")
    oc = order_code(order_id)
    await update.callback_query.answer(f"{oc} отклонён", show_alert=True)
    order = await get_order(order_id)
    if order:
        _, user_id, pname, price, status, _ = order
        try:
            await context.bot.send_message(user_id, f"Ваш заказ {oc} отклонён. Если это ошибка — свяжитесь с поддержкой.")
        except Exception:
            pass

@admin_only
async def admin_list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await list_active_products()
    if not rows:
        txt = "Товаров нет."
    else:
        lines = [f"{pid}. {name} — {price}₽" for pid, name, price, _ in rows]
        txt = "Список товаров:\n" + "\n".join(lines)
    await update.callback_query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]]))

@admin_only
async def admin_add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_product_step"] = "name"
    await update.callback_query.edit_message_text("Введите название товара в одном сообщении:")

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("add_product_step")
    if step:
        if update.effective_user.id not in ADMIN_IDS:
            return
        if step == "name":
            context.user_data["new_product_name"] = update.message.text.strip()
            context.user_data["add_product_step"] = "price"
            await update.message.reply_text("Введите цену (целое число в рублях):")
            return
        elif step == "price":
            try:
                price = int(update.message.text.strip())
            except ValueError:
                await update.message.reply_text("Нужно целое число. Попробуйте ещё раз:")
                return
            context.user_data["new_product_price"] = price
            context.user_data["add_product_step"] = "desc"
            await update.message.reply_text("Добавьте описание (или '-' для пустого):")
            return
        elif step == "desc":
            desc = update.message.text.strip()
            if desc == "-":
                desc = ""
            async with get_db() as db:
                await db.execute("INSERT INTO products (name, price, description) VALUES (?, ?, ?);", (context.user_data["new_product_name"], context.user_data["new_product_price"], desc))
            context.user_data.pop("add_product_step", None)
            await update.message.reply_text("Товар добавлен ✅")
            return
    if update.effective_user.id not in ADMIN_IDS:
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, f"📩 Сообщение от @{update.effective_user.username or update.effective_user.id}: {update.message.text}")
            except Exception:
                pass

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data

    if data == "catalog":
        return await catalog(update, context)
    if data == "my_orders":
        return await my_orders(update, context)
    if data == "help":
        return await help_cmd(update, context)
    if data == "back_main":
        return await start(update, context)

    if data == "admin_back":
        return await admin_menu(update, context)
    if data == "admin_orders_pending":
        return await admin_orders_pending(update, context)
    if data == "admin_add_product":
        return await admin_add_product_start(update, context)
    if data == "admin_list_products":
        return await admin_list_products(update, context)

    if data.startswith("prod_"):
        pid = int(data.split("_")[1])
        return await product_view(update, context, pid)
    if data.startswith("buy_"):
        pid = int(data.split("_")[1])
        return await buy_product(update, context, pid)
    if data.startswith("paid_"):
        await q.answer("Если вы ещё не отправили скриншот — пришлите его сообщением сюда.")
        return
    if data.startswith("admin_mark_paid_"):
        oid = int(data.split("_")[3])
        return await admin_mark_paid(update, context, oid)
    if data.startswith("admin_reject_"):
        oid = int(data.split("_")[2])
        return await admin_reject(update, context, oid)

    await q.answer("Неизвестная команда")

async def init():
    await migrate()

def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is not set")
    app = Application.builder().token(BOT_TOKEN).build()
    app.post_init = init

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_menu))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_proof))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
