import os

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
STRIPE_KEY = os.getenv("STRIPE_KEY")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_SECRET")
NOWPAY_API_KEY = os.getenv("NOWPAY_API_KEY")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x]
ADMIN_KEY = os.getenv("ADMIN_KEY","admin123")
USD_PER_CREDIT = float(os.getenv("USD_PER_CREDIT","1"))
