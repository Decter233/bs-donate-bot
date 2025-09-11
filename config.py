import os
from dotenv import load_dotenv

# Загружаем .env, если файл есть
load_dotenv()

# --- Бот ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  # токен от BotFather
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# --- Платежи ---
PAYMENT_TEXT = os.getenv("PAYMENT_TEXT", "Оплатите заказ {order_code} и отправьте чек.")
QIWI_NUMBER = os.getenv("QIWI_NUMBER", "")
YOOMONEY_WALLET = os.getenv("YOOMONEY_WALLET", "")

# --- База данных ---
DB_PATH = os.getenv("DB_PATH", "shop.sqlite3")

# --- Вебхук ---
BOT_URL = os.getenv("https://bs-donate-bot.onrender.com")  # публичный URL Render
PORT = int(os.getenv("PORT", 10000))  # порт Render
