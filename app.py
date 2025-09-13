import os
from telegram.ext import Application, CommandHandler

# Загружаем токен из переменных окружения
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не найдена!")

# Создаём приложение
app = Application.builder().token(TOKEN).build()

# Хендлер команды /start
async def start(update, context):
    await update.message.reply_text("Бот запущен ✅")

# Регистрируем хендлер
app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", "10000"))
    WEBHOOK_URL = "https://bs-donate-bot.onrender.com/webhook"  # без токена и лишних слэшей

    print(f"Устанавливаю вебхук: {WEBHOOK_URL}")

    # Запуск приложения с вебхуком
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True
    )
