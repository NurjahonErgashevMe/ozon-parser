#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный файл приложения Ozon Parser
Запуск: python app.py
"""

import sys
import os
import logging
import signal
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from src.core.app_manager import AppManager
from src.utils.logger import setup_logging
from src.config.settings import Settings

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\nПолучен сигнал завершения. Закрытие приложения...")
    if hasattr(signal_handler, 'app_manager'):
        signal_handler.app_manager.shutdown()
    sys.exit(0)

def main():
    """Главная функция приложения"""
    try:
        # Настройка логирования
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Запуск Ozon Parser")
        
        # Загрузка настроек
        settings = Settings()
        
        # Создание менеджера приложения
        app_manager = AppManager(settings)
        signal_handler.app_manager = app_manager
        
        # Регистрация обработчиков сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # URL категории для парсинга
        category_url = "https://ozon.ru/category/sistemnye-bloki-15704/?__rr=2&abt_att=1&category_was_predicted=true&deny_category_prediction=true&from_global=true&origin_referer=www.ozon.ru&text=комьютер"
        
        logger.info(f"Начинаем парсинг категории: {category_url}")
        logger.info(f"Максимум товаров: {settings.MAX_PRODUCTS}")
        logger.info(f"Максимум воркеров: {settings.MAX_WORKERS}")
        
        # Запуск парсинга
        success = app_manager.start_parsing(category_url)
        
        if success:
            logger.info("Парсинг завершен успешно")
        else:
            logger.error("Ошибка парсинга")
        
    except KeyboardInterrupt:
        logger.info("Получен Ctrl+C, завершение работы...")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise
    finally:
        if 'app_manager' in locals():
            app_manager.shutdown()
        logger.info("Приложение завершено")

if __name__ == "__main__":
    main()