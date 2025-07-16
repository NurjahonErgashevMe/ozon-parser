"""
Вкладка разработчика
"""
import tkinter as tk
from tkinter import ttk
import webbrowser
import logging

logger = logging.getLogger(__name__)

class DeveloperTab:
    """Вкладка информации о разработчике"""
    
    def __init__(self, parent, app_manager):
        self.parent = parent
        self.app_manager = app_manager
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создание виджетов вкладки"""
        self.frame = ttk.Frame(self.parent)
        
        # Заголовок
        title_label = ttk.Label(self.frame, text="👨‍💻 Информация о разработчике", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=20)
        
        # Информация о приложении
        app_info_frame = ttk.LabelFrame(self.frame, text="📱 О приложении", padding=20)
        app_info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(app_info_frame, text="Ozon Parser Manager", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W)
        ttk.Label(app_info_frame, text="Версия: 1.0", 
                 font=('Arial', 12)).pack(anchor=tk.W, pady=2)
        ttk.Label(app_info_frame, text="Парсер товаров с Ozon.ru с GUI интерфейсом", 
                 font=('Arial', 11)).pack(anchor=tk.W, pady=2)
        
        # Контакты разработчика
        contact_frame = ttk.LabelFrame(self.frame, text="📞 Контакты разработчика", padding=20)
        contact_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Настройка стиля для ссылок
        style = ttk.Style()
        style.configure("Link.TLabel", foreground="blue", font=('Arial', 12, 'underline'))
        
        # Telegram
        ttk.Label(contact_frame, text="Telegram:", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        telegram_link = ttk.Label(contact_frame, text="@NurjahonErgashevMe", 
                                 style="Link.TLabel", cursor="hand2")
        telegram_link.pack(anchor=tk.W, padx=20, pady=(0, 15))
        telegram_link.bind("<Button-1>", lambda e: self._open_link("https://t.me/NurjahonErgashevMe"))
        
        # Kwork
        ttk.Label(contact_frame, text="Kwork:", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        kwork_link = ttk.Label(contact_frame, text="https://kwork.ru/user/nurjahonergashevme", 
                              style="Link.TLabel", cursor="hand2")
        kwork_link.pack(anchor=tk.W, padx=20, pady=(0, 15))
        kwork_link.bind("<Button-1>", lambda e: self._open_link("https://kwork.ru/user/nurjahonergashevme"))
        
        # Возможности приложения
        features_frame = ttk.LabelFrame(self.frame, text="⚡ Возможности", padding=20)
        features_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        features_text = """🔍 Парсинг ссылок товаров с категорий Ozon
📊 Извлечение данных товаров через API Ozon
🤖 Интеграция с Telegram ботом для уведомлений
🖥️ GUI интерфейс для управления
⚡ Многопоточная обработка (до 10 воркеров)
📝 Подробное логирование
💾 Сохранение результатов в JSON
🎯 Настраиваемые параметры парсинга"""
        
        features_label = ttk.Label(features_frame, text=features_text, 
                                  justify=tk.LEFT, font=('Arial', 11))
        features_label.pack(anchor=tk.W)
        
        # Логотип/заглушка
        logo_frame = ttk.Frame(self.frame)
        logo_frame.pack(pady=20)
        
        logo_label = ttk.Label(logo_frame, text="🛒 OZON PARSER", 
                              font=('Arial', 20, 'bold'), 
                              foreground="darkblue",
                              borderwidth=2, 
                              relief="solid", 
                              padding=10)
        logo_label.pack()
        
        # Кнопки действий
        actions_frame = ttk.Frame(self.frame)
        actions_frame.pack(pady=15)
        
        ttk.Button(actions_frame, text="📧 Связаться в Telegram", 
                  command=lambda: self._open_link("https://t.me/NurjahonErgashevMe")).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="💼 Заказать работу на Kwork", 
                  command=lambda: self._open_link("https://kwork.ru/user/nurjahonergashevme")).pack(side=tk.LEFT, padx=5)
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def _open_link(self, url):
        """Открытие ссылки в браузере"""
        try:
            webbrowser.open(url)
            logger.info(f"Открыта ссылка: {url}")
        except Exception as e:
            logger.error(f"Ошибка открытия ссылки {url}: {e}")