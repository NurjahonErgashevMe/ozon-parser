"""
Вкладка управления
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import logging

logger = logging.getLogger(__name__)

class ControlTab:
    """Вкладка управления парсингом и ботом"""
    
    def __init__(self, parent, app_manager):
        self.parent = parent
        self.app_manager = app_manager
        self.main_window = None
        
        # Переменные статуса
        self.bot_status_var = tk.StringVar(value="🔴 Не запущен")
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создание виджетов вкладки"""
        self.frame = ttk.Frame(self.parent)
        
        # Статус
        status_group = ttk.LabelFrame(self.frame, text="📊 Статус бота", padding=15)
        status_group.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(status_group, text="Telegram бот:", font=('Arial', 14, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(status_group, textvariable=self.bot_status_var, font=('Arial', 14)).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        

        
        # Управление ботом
        bot_group = ttk.LabelFrame(self.frame, text="🤖 Управление ботом", padding=15)
        bot_group.pack(fill=tk.X, padx=10, pady=20)
        
        bot_buttons_frame = ttk.Frame(bot_group)
        bot_buttons_frame.pack(fill=tk.X)
        
        self.start_bot_btn = ttk.Button(bot_buttons_frame, text="▶️ Запустить бота", 
                                       command=self._start_bot)
        self.start_bot_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_bot_btn = ttk.Button(bot_buttons_frame, text="⏹️ Остановить бота", 
                                      command=self._stop_bot, state=tk.DISABLED)
        self.stop_bot_btn.pack(side=tk.LEFT, padx=5)
        
        self.restart_bot_btn = ttk.Button(bot_buttons_frame, text="🔄 Перезапустить бота", 
                                         command=self._restart_bot, state=tk.DISABLED)
        self.restart_bot_btn.pack(side=tk.LEFT, padx=5)
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def update_status(self, status_data):
        """Обновление статуса"""
        try:
            # Обновляем статус бота
            if status_data.get('telegram_bot_active'):
                self.bot_status_var.set("🟢 Запущен")
                self.start_bot_btn.config(state=tk.DISABLED)
                self.stop_bot_btn.config(state=tk.NORMAL)
                self.restart_bot_btn.config(state=tk.NORMAL)
            else:
                self.bot_status_var.set("🔴 Не запущен")
                self.start_bot_btn.config(state=tk.NORMAL)
                self.stop_bot_btn.config(state=tk.DISABLED)
                self.restart_bot_btn.config(state=tk.DISABLED)
                
        except Exception as e:
            logger.debug(f"Ошибка обновления статуса: {e}")
    

    
    def set_main_window(self, main_window):
        """Установка ссылки на главное окно"""
        self.main_window = main_window
    

    

    

    
    def _start_bot(self):
        """Запуск Telegram бота"""
        def start_async():
            try:
                if not self.main_window:
                    messagebox.showerror("Ошибка", "Не удалось получить конфигурацию")
                    return
                
                config = self.main_window.get_config_data()
                bot_token = config.get('bot_token')
                user_ids = config.get('user_ids', [])
                
                if not bot_token or not user_ids:
                    messagebox.showerror("Ошибка", "Настройте токен бота и User ID на вкладке 'Конфигурация'")
                    return
                
                success = self.app_manager.start_telegram_bot(bot_token, user_ids)
                
                if success:
                    messagebox.showinfo("Успех", "Telegram бот запущен")
                else:
                    messagebox.showerror("Ошибка", "Ошибка запуска бота")
                    
            except Exception as e:
                logger.error(f"Ошибка запуска бота: {e}")
                messagebox.showerror("Ошибка", f"Ошибка: {e}")
        
        threading.Thread(target=start_async, daemon=True).start()
    
    def _stop_bot(self):
        """Остановка Telegram бота"""
        try:
            self.app_manager.stop_telegram_bot()
            messagebox.showinfo("Успех", "Telegram бот остановлен")
        except Exception as e:
            logger.error(f"Ошибка остановки бота: {e}")
            messagebox.showerror("Ошибка", f"Ошибка: {e}")
    
    def _restart_bot(self):
        """Перезапуск Telegram бота"""
        def restart_async():
            try:
                # Останавливаем бота
                self.app_manager.stop_telegram_bot()
                
                if not self.main_window:
                    messagebox.showerror("Ошибка", "Не удалось получить конфигурацию")
                    return
                
                config = self.main_window.get_config_data()
                bot_token = config.get('bot_token')
                user_ids = config.get('user_ids', [])
                
                if not bot_token or not user_ids:
                    messagebox.showerror("Ошибка", "Настройте токен бота и User ID на вкладке 'Конфигурация'")
                    return
                
                # Запускаем заново
                success = self.app_manager.start_telegram_bot(bot_token, user_ids)
                
                if success:
                    messagebox.showinfo("Успех", "Telegram бот перезапущен")
                else:
                    messagebox.showerror("Ошибка", "Ошибка перезапуска бота")
                    
            except Exception as e:
                logger.error(f"Ошибка перезапуска бота: {e}")
                messagebox.showerror("Ошибка", f"Ошибка: {e}")
        
        threading.Thread(target=restart_async, daemon=True).start()