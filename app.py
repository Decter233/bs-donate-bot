from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")  # токен из Render Secrets

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я донат-бот для Brawl Stars!")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))  # Render предоставляет переменную PORT
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,  # можно использовать токен как секретный путь
        webhook_url=f"https://https://bs-donate-bot.onrender.com/{7315170970:AAH2dzGe_BN1Ti9oumTlZ0po4FhL7t8GehE}"
    )
