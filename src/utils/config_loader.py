from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def load_telegram_config() -> Tuple[Optional[str], Optional[str]]:
    """Загружает TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID из config.txt"""
    config_path = Path(__file__).parent.parent.parent / "config.txt"
    
    if not config_path.exists():
        logger.warning("config.txt не найден")
        return None, None
    
    bot_token = None
    chat_id = None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('TELEGRAM_BOT_TOKEN='):
                    bot_token = line.split('=', 1)[1]
                elif line.startswith('TELEGRAM_CHAT_ID='):
                    chat_id = line.split('=', 1)[1]
    except Exception as e:
        logger.error(f"Ошибка чтения config.txt: {e}")
        return None, None
    
    return bot_token, chat_id