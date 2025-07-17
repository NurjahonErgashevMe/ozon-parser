"""
Главное окно GUI приложения
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from typing import TYPE_CHECKING

from .tabs import ConfigTab, ControlTab, LogsTab, DeveloperTab

if TYPE_CHECKING:
    from ..core.app_manager import AppManager

logger = logging.getLogger(__name__)

class MainWindow:
    """Главное окно приложения"""
    
    def __init__(self, app_manager: 'AppManager'):
        self.app_manager = app_manager
        self.root = None
        self.notebook = None
        
        # Вкладки
        self.config_tab = None
        self.control_tab = None
        self.logs_tab = None
        self.developer_tab = None
        
        logger.info("GUI инициализирован")
    
    def run(self):
        """Запуск GUI"""
        try:
            self.root = tk.Tk()
            self.root.title("🤖 Telegram Bot Manager v1.0")
            self.root.geometry("900x700")
            self.root.minsize(800, 600)
            
            # Центрирование окна
            self.root.eval('tk::PlaceWindow . center')
            
            # Обработчик закрытия окна
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            self._create_widgets()
            self._start_status_updater()
            
            logger.info("GUI запущен")
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Ошибка GUI: {e}")
            messagebox.showerror("Ошибка", f"Критическая ошибка GUI: {e}")
    
    def _create_widgets(self):
        """Создание виджетов"""
        # Создаем notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создаем вкладки
        self.config_tab = ConfigTab(self.notebook, self.app_manager)
        self.control_tab = ControlTab(self.notebook, self.app_manager)
        self.logs_tab = LogsTab(self.notebook, self.app_manager)
        self.developer_tab = DeveloperTab(self.notebook, self.app_manager)
        
        # Устанавливаем связи между вкладками
        self.control_tab.set_main_window(self)
        
        # Добавляем вкладки в notebook
        self.notebook.add(self.config_tab.get_frame(), text="⚙️ Конфигурация")
        self.notebook.add(self.control_tab.get_frame(), text="🎮 Управление")
        self.notebook.add(self.logs_tab.get_frame(), text="📝 Логи")
        self.notebook.add(self.developer_tab.get_frame(), text="👨‍💻 Разработчик")
        
        # Статусная строка
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
    

    

    

    

    
    def _start_status_updater(self):
        """Запуск обновления статуса"""
        def update_status():
            try:
                status = self.app_manager.get_status()
                
                # Обновляем статус в вкладке управления
                if self.control_tab:
                    self.control_tab.update_status(status)
                
                # Обновляем статусную строку
                if status.get('telegram_bot_active'):
                    self.status_var.set("🤖 Бот активен")
                else:
                    self.status_var.set("✅ Готов к работе")
                
            except Exception as e:
                logger.debug(f"Ошибка обновления статуса: {e}")
            
            # Планируем следующее обновление
            if self.root:
                self.root.after(2000, update_status)
        
        # Запускаем первое обновление
        self.root.after(1000, update_status)
    
    def get_config_data(self):
        """Получение данных конфигурации из вкладки"""
        if self.config_tab:
            return {
                'bot_token': self.config_tab.bot_token_var.get().strip(),
                'user_id': self.config_tab.user_id_var.get().strip()
            }
        return {}
    
    
    
    def _on_closing(self):
        try:
            if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
                logger.info("Закрытие приложения...")

                # 🚀 shutdown in a daemon thread so GUI stays responsive
                threading.Thread(target=self.app_manager.shutdown, daemon=True).start()

                # schedule actual window destroy
                self.root.after(200, self.root.destroy)
        except Exception as e:
            logger.error(f"Ошибка закрытия: {e}")
            self.root.destroy()
    
    def get_main_window(self):
        """Возвращает ссылку на главное окно"""
        return self