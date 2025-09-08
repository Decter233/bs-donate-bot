import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").replace(";", ",").split(",") if x.strip().isdigit()]
QIWI_NUMBER = os.getenv("QIWI_NUMBER", "")
YOOMONEY_WALLET = os.getenv("YOOMONEY_WALLET", "")
PAYMENT_TEXT = os.getenv("PAYMENT_TEXT", "Переведите сумму и укажите комментарий {order_code}. Затем отправьте скриншот.")
DB_PATH = os.getenv("DB_PATH", "shop.sqlite3")