from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def load_telegram_config() -> Tuple[Optional[str], Optional[str]]:
    """Загружает TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID из config.txt"""
    import sys
    
    # Определяем путь к config.txt
    if getattr(sys, 'frozen', False):
        # Если приложение скомпилировано (PyInstaller)
        config_path = Path(sys.executable).parent / "config.txt"
    else:
        # Если запущено из исходников
        config_path = Path(__file__).parent.parent.parent / "config.txt"
    
    logger.info(f"Поиск config.txt по пути: {config_path}")
    
    if not config_path.exists():
        logger.warning(f"config.txt не найден по пути: {config_path}")
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
