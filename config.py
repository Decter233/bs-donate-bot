import os
from dotenv import load_dotenv

load_dotenv()  # загружает .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
PAYMENT_TEXT = os.getenv("PAYMENT_TEXT", "Оплатите заказ {order_code} и отправьте чек.")
QIWI_NUMBER = os.getenv("QIWI_NUMBER", "")
YOOMONEY_WALLET = os.getenv("YOOMONEY_WALLET", "")
DB_PATH = os.getenv("DB_PATH", "shop.sqlite3")
