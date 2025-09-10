from telegram.ext import Application, CommandHandler
from config import BOT_TOKEN

# Тестовая команда /start
async def start(update, context):
    await update.message.reply_text("✅ Бот работает и отвечает на команды!")

def main():
    # Создаём приложение без Updater
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчик команды /start
    app.add_handler(CommandHandler("start", start))

    # Запускаем бота
    app.run_polling()

if __name__ == "__main__":
    main()
