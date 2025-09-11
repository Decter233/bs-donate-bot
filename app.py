import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Купить монеты", callback_data='buy_coins')],
        [InlineKeyboardButton("Купить скины", callback_data='buy_skins')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выбери, что хочешь купить:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "buy_coins":
        await query.edit_message_text("Вы выбрали покупку монет. Инструкции: ...")
    elif query.data == "buy_skins":
        await query.edit_message_text("Вы выбрали покупку скинов. Инструкции: ...")
    else:
        await query.edit_message_text("Неизвестная опция.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"Ваше сообщение: {text}")

# --- Основная функция ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
