import os
from dotenv import load_dotenv

load_dotenv()

# Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "cherryspin.db")

# Webhook settings
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://your-render-url.onrender.com")
WEBHOOK_PATH = f"/webhook/{TELEGRAM_BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Admins
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")