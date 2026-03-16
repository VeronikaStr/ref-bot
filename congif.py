import os

# Токен бота из BotFather
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "тут_твой_токен")

# Путь webhook (любой, уникальный)
WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH", "/webhook")

# Полный URL для webhook (домен Render + путь)
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}")

# Уровень логирования
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
