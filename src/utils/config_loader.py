from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import logging
import sys

logger = logging.getLogger(__name__)

def get_config_path() -> Path:
    """Возвращает путь к файлу конфигурации"""
    if getattr(sys, 'frozen', False):
        # Если приложение скомпилировано (PyInstaller)
        config_path = Path(sys.executable).parent / "config.txt"
    else:
        # Если запущено из исходников
        config_path = Path(__file__).parent.parent.parent / "config.txt"
    
    return config_path

def read_config() -> Dict[str, str]:
    """Читает файл конфигурации и возвращает словарь с настройками"""
    config_path = get_config_path()
    logger.info(f"Поиск config.txt по пути: {config_path}")
    
    config = {}
    
    if not config_path.exists():
        logger.warning(f"config.txt не найден по пути: {config_path}")
        return config
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key] = value
    except Exception as e:
        logger.error(f"Ошибка чтения config.txt: {e}")
    
    return config

def write_config(new_config: Dict[str, Any]) -> bool:
    """Записывает настройки в файл конфигурации"""
    config_path = get_config_path()
    
    try:
        # Сначала читаем существующий файл, чтобы сохранить другие настройки
        existing_config = read_config()
        # Обновляем существующие настройки новыми
        for key, value in new_config.items():
            existing_config[key] = str(value)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            for key, value in existing_config.items():
                f.write(f"{key}={value}\n")
        return True
    except Exception as e:
        logger.error(f"Ошибка записи в config.txt: {e}")
        return False

def load_telegram_config() -> Tuple[Optional[str], Optional[str]]:
    """Загружает TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID из config.txt"""
    config = read_config()
    
    bot_token = config.get('TELEGRAM_BOT_TOKEN')
    chat_id = config.get('TELEGRAM_CHAT_ID')
    
    return bot_token, chat_id

def load_telegram_config_multi() -> Tuple[Optional[str], list]:
    """Загружает TELEGRAM_BOT_TOKEN и список TELEGRAM_CHAT_ID из config.txt"""
    config = read_config()
    
    bot_token = config.get('TELEGRAM_BOT_TOKEN')
    chat_ids_str = config.get('TELEGRAM_CHAT_ID', '')
    
    # Парсим список User ID
    chat_ids = []
    if chat_ids_str:
        chat_ids = [uid.strip() for uid in chat_ids_str.split(',') if uid.strip()]
    
    return bot_token, chat_ids
