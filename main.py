#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный файл приложения Ozon Parser - запуск GUI
Запуск: python main.py
"""

import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import Settings
from src.core.app_manager import AppManager
from src.gui.main_window import MainWindow
from src.utils.logger import setup_logging

def main():
    """Запуск GUI для управления Telegram ботом"""
    try:
        # Настройка логирования
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Запуск Telegram Bot Manager GUI")
        
        # Загрузка настроек
        settings = Settings()
        
        # Создание менеджера приложения
        app_manager = AppManager(settings)
        
        # Создание и запуск GUI
        gui = MainWindow(app_manager)
        gui.run()
        
    except Exception as e:
        print(f"❌ Ошибка запуска GUI: {e}")
        logging.error(f"Критическая ошибка GUI: {e}")

if __name__ == "__main__":
    main()