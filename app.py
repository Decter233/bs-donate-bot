import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from telegram import Update

from config import BOT_TOKEN
from db import migrate

# --------------- тут твой код (все функции start, catalog, buy_product и т.д.) ----------------

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(catalog, pattern="^catalog$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: asyncio.create_task(product_view(u, c, int(c.match.group(1)))), pattern=r"^prod_(\d+)$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: asyncio.create_task(buy_product(u, c, int(c.match.group(1)))), pattern=r"^buy_(\d+)$"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_proof))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    asyncio.run(migrate())
    main()
