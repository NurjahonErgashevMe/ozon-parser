import os
from pathlib import Path
from typing import Optional

class Settings:
    BASE_DIR = Path(__file__).parent.parent.parent
    OUTPUT_DIR = BASE_DIR / "output"
    LOGS_DIR = BASE_DIR / "logs"

    MAX_PRODUCTS = 50
    MAX_WORKERS = 5
    WORKER_TIMEOUT = 30

    HEADLESS = True
    IMPLICIT_WAIT = 10
    PAGE_LOAD_TIMEOUT = 30

    OZON_BASE_URL = "https://www.ozon.ru"
    OZON_API_URL = "https://www.ozon.ru/api/composer-api.bx/page/json/v2"

    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_USER_ID: Optional[str] = None

    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def __init__(self):
        self.ensure_directories()
    
    def ensure_directories(self):
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
    
    def update_telegram_settings(self, bot_token: str, user_id: str):
        self.TELEGRAM_BOT_TOKEN = bot_token
        self.TELEGRAM_USER_ID = user_id