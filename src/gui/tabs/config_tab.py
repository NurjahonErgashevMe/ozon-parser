"""
Вкладка конфигурации
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

class ConfigTab:
    """Вкладка настроек"""
    
    def __init__(self, parent, app_manager):
        self.parent = parent
        self.app_manager = app_manager
        
        # Переменные
        self.bot_token_var = tk.StringVar()
        self.user_id_var = tk.StringVar()
        self.show_token_var = tk.BooleanVar()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создание виджетов вкладки"""
        self.frame = ttk.Frame(self.parent)
        
        # Telegram настройки
        telegram_group = ttk.LabelFrame(self.frame, text="🤖 Настройки Telegram бота", padding=15)
        telegram_group.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(telegram_group, text="Токен бота:", font=('Arial', 12)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.token_entry = ttk.Entry(telegram_group, textvariable=self.bot_token_var, width=60, show="*")
        self.token_entry.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        show_token_cb = ttk.Checkbutton(telegram_group, text="Показать токен", 
                                       variable=self.show_token_var, 
                                       command=self._toggle_token_visibility)
        show_token_cb.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(telegram_group, text="User ID:", font=('Arial', 12)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.user_id_entry = ttk.Entry(telegram_group, textvariable=self.user_id_var, width=60)
        self.user_id_entry.grid(row=2, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        telegram_group.columnconfigure(1, weight=1)
        
        # Кнопки
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=15)
        
        ttk.Button(buttons_frame, text="💾 Сохранить", command=self._save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="📁 Загрузить", command=self._load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🗑️ Очистить", command=self._clear_fields).pack(side=tk.LEFT, padx=5)
        
        # Информация
        info_frame = ttk.LabelFrame(self.frame, text="📋 Как получить данные", padding=15)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = """1. Создайте бота через @BotFather в Telegram:
   • Отправьте команду /newbot
   • Следуйте инструкциям и получите токен

2. Узнайте свой User ID:
   • Напишите боту @userinfobot
   • Или найдите свой ID через @getmyid_bot

3. Введите полученные данные в поля выше
4. Нажмите 'Сохранить' для сохранения настроек"""
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT, font=('Arial', 10))
        info_label.pack(anchor=tk.W)
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def _toggle_token_visibility(self):
        """Переключение видимости токена"""
        if self.show_token_var.get():
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="*")
    
    def _get_config_path(self):
        """Получение пути к файлу конфигурации"""
        if getattr(sys, 'frozen', False):
            # Если приложение скомпилировано (PyInstaller)
            return Path(sys.executable).parent / "config.txt"
        else:
            # Если запущено из исходников - используем тот же метод, что и в config_loader.py
            return Path(__file__).parent.parent.parent.parent / "config.txt"
    
    def _save_config(self):
        """Сохранение конфигурации"""
        try:
            bot_token = self.bot_token_var.get().strip()
            user_id = self.user_id_var.get().strip()
            
            if not bot_token or not user_id:
                messagebox.showwarning("Предупреждение", "Заполните все поля")
                return
            
            config_path = self._get_config_path()
            logger.info(f"Сохранение конфигурации в: {config_path}")
            
            # Сохраняем конфигурацию
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(f"TELEGRAM_BOT_TOKEN={bot_token}\n")
                f.write(f"TELEGRAM_CHAT_ID={user_id}\n")
            
            messagebox.showinfo("Успех", "Настройки сохранены!")
            logger.info(f"Настройки сохранены в {config_path}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {e}")
    
    def _load_config(self):
        """Загрузка существующей конфигурации"""
        try:
            config_path = self._get_config_path()
            logger.info(f"Загрузка конфигурации из: {config_path}")
            
            if not config_path.exists():
                messagebox.showwarning("Предупреждение", f"Файл конфигурации не найден: {config_path}")
                return
            
            # Чтение файла конфигурации
            config = {}
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
            
            # Заполняем поля
            if "TELEGRAM_BOT_TOKEN" in config:
                self.bot_token_var.set(config["TELEGRAM_BOT_TOKEN"])
            
            if "TELEGRAM_CHAT_ID" in config:
                self.user_id_var.set(config["TELEGRAM_CHAT_ID"])
            
            messagebox.showinfo("Успех", "Конфигурация загружена!")
            logger.info("Конфигурация загружена из файла")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить конфигурацию: {e}")
    
    def _clear_fields(self):
        """Очистка полей"""
        self.bot_token_var.set("")
        self.user_id_var.set("")
        logger.info("Поля конфигурации очищены")