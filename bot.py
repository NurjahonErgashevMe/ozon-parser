#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск Telegram бота
Запуск: python bot.py
"""

import logging
from pathlib import Path
from src.config.settings import Settings
from src.core.app_manager import AppManager
from src.telegram.bot_manager import TelegramBotManager
from src.utils.logger import setup_logging
from src.utils.config_loader import load_telegram_config

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        bot_token, chat_id = load_telegram_config()
        
        if not bot_token:
            print("❌ Укажите TELEGRAM_BOT_TOKEN в config.txt")
            return
            
        if not chat_id:
            print("❌ Укажите TELEGRAM_CHAT_ID в config.txt")
            return
        
        settings = Settings()
        app_manager = AppManager(settings)
        
        bot_manager = TelegramBotManager(bot_token, chat_id, app_manager)
        
        print("🤖 Запуск Telegram бота...")
        
        if bot_manager.start():
            print("✅ Telegram бот запущен успешно")
            
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Остановка бота...")
                bot_manager.stop()
                app_manager.shutdown()
        else:
            print("❌ Ошибка запуска бота")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()