"""
Тестовый файл для проверки GUI
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.gui.main_window import MainWindow
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Заглушка для AppManager
class MockAppManager:
    def __init__(self):
        self.settings = MockSettings()
    
    def get_status(self):
        return {
            'is_running': False,
            'telegram_bot_active': False,
            'progress': '',
            'last_results': None
        }
    
    def start_parsing(self, url):
        print(f"Mock: Запуск парсинга для {url}")
        return True
    
    def stop_parsing(self):
        print("Mock: Остановка парсинга")
        return True
    
    def restart_parsing(self, url):
        print(f"Mock: Перезапуск парсинга для {url}")
        return True
    
    def start_telegram_bot(self, token, user_id):
        print(f"Mock: Запуск бота с токеном {token[:10]}... для пользователя {user_id}")
        return True
    
    def stop_telegram_bot(self):
        print("Mock: Остановка бота")
        return True
    
    def shutdown(self):
        print("Mock: Завершение работы")

class MockSettings:
    def __init__(self):
        self.MAX_PRODUCTS = 100
        self.MAX_WORKERS = 5

if __name__ == "__main__":
    # Создаем заглушку менеджера
    app_manager = MockAppManager()
    
    # Создаем и запускаем GUI
    gui = MainWindow(app_manager)
    gui.run()