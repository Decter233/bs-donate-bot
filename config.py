import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("7315170970:AAH2dzGe_BN1Ti9oumTlZ0po4FhL7t8GehE")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
PAYMENT_TEXT = os.getenv("PAYMENT_TEXT", "Оплатите заказ {order_code} и отправьте чек.")
QIWI_NUMBER = os.getenv("QIWI_NUMBER", "")
YOOMONEY_WALLET = os.getenv("YOOMONEY_WALLET", "")
