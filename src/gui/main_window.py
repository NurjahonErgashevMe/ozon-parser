"""
Главное окно GUI приложения
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.app_manager import AppManager

logger = logging.getLogger(__name__)

class MainWindow:
    """Главное окно приложения"""
    
    def __init__(self, app_manager: 'AppManager'):
        self.app_manager = app_manager
        self.root = None
        self.notebook = None
        
        # Переменные для настроек
        self.bot_token_var = tk.StringVar()
        self.user_id_var = tk.StringVar()
        self.category_url_var = tk.StringVar(value="https://ozon.ru/category/sistemnye-bloki-15704/")
        self.max_products_var = tk.IntVar(value=100)
        self.max_workers_var = tk.IntVar(value=5)
        
        # Переменные для статуса
        self.parsing_status_var = tk.StringVar(value="Остановлен")
        self.bot_status_var = tk.StringVar(value="Не запущен")
        
        # Лог виджет
        self.log_text = None
        
        # Обработчик логов
        self.log_handler = None
        
        logger.info("GUI инициализирован")
    
    def run(self):
        """Запуск GUI"""
        try:
            self.root = tk.Tk()
            self.root.title("Ozon Parser v1.0")
            self.root.geometry("800x600")
            self.root.minsize(600, 400)
            
            # Обработчик закрытия окна
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            self._create_widgets()
            self._setup_logging()
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
        
        # Вкладки
        self._create_config_tab()
        self._create_control_tab()
        self._create_logs_tab()
    
    def _create_config_tab(self):
        """Вкладка конфигурации"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Конфигурация")
        
        # Telegram настройки
        telegram_group = ttk.LabelFrame(config_frame, text="Настройки Telegram бота", padding=10)
        telegram_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(telegram_group, text="Токен бота:").grid(row=0, column=0, sticky=tk.W, pady=2)
        bot_token_entry = ttk.Entry(telegram_group, textvariable=self.bot_token_var, width=50, show="*")
        bot_token_entry.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=2)
        
        ttk.Label(telegram_group, text="User ID:").grid(row=1, column=0, sticky=tk.W, pady=2)
        user_id_entry = ttk.Entry(telegram_group, textvariable=self.user_id_var, width=50)
        user_id_entry.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=2)
        
        telegram_group.columnconfigure(1, weight=1)
        
        # Настройки парсинга
        parsing_group = ttk.LabelFrame(config_frame, text="Настройки парсинга", padding=10)
        parsing_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(parsing_group, text="URL категории:").grid(row=0, column=0, sticky=tk.W, pady=2)
        url_entry = ttk.Entry(parsing_group, textvariable=self.category_url_var, width=50)
        url_entry.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=2)
        
        ttk.Label(parsing_group, text="Макс. товаров:").grid(row=1, column=0, sticky=tk.W, pady=2)
        products_spin = ttk.Spinbox(parsing_group, from_=1, to=1000, textvariable=self.max_products_var, width=10)
        products_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(parsing_group, text="Макс. воркеров:").grid(row=2, column=0, sticky=tk.W, pady=2)
        workers_spin = ttk.Spinbox(parsing_group, from_=1, to=10, textvariable=self.max_workers_var, width=10)
        workers_spin.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        parsing_group.columnconfigure(1, weight=1)
        
        # Кнопки
        buttons_frame = ttk.Frame(config_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Сохранить настройки", command=self._save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Тест Telegram", command=self._test_telegram).pack(side=tk.LEFT, padx=5)
    
    def _create_control_tab(self):
        """Вкладка управления"""
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text="Управление")
        
        # Статус
        status_group = ttk.LabelFrame(control_frame, text="Статус", padding=10)
        status_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(status_group, text="Парсинг:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(status_group, textvariable=self.parsing_status_var).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(status_group, text="Telegram бот:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(status_group, textvariable=self.bot_status_var).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Управление парсингом
        parsing_group = ttk.LabelFrame(control_frame, text="Управление парсингом", padding=10)
        parsing_group.pack(fill=tk.X, padx=10, pady=5)
        
        buttons_frame = ttk.Frame(parsing_group)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="Запустить парсинг", command=self._start_parsing).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Остановить парсинг", command=self._stop_parsing).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Перезапустить", command=self._restart_parsing).pack(side=tk.LEFT, padx=5)
        
        # Управление ботом
        bot_group = ttk.LabelFrame(control_frame, text="Управление Telegram ботом", padding=10)
        bot_group.pack(fill=tk.X, padx=10, pady=5)
        
        bot_buttons_frame = ttk.Frame(bot_group)
        bot_buttons_frame.pack(fill=tk.X)
        
        ttk.Button(bot_buttons_frame, text="Запустить бота", command=self._start_bot).pack(side=tk.LEFT, padx=5)
        ttk.Button(bot_buttons_frame, text="Остановить бота", command=self._stop_bot).pack(side=tk.LEFT, padx=5)
        
        # Результаты
        results_group = ttk.LabelFrame(control_frame, text="Последние результаты", padding=10)
        results_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.results_text = scrolledtext.ScrolledText(results_group, height=8, state=tk.DISABLED)
        self.results_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_logs_tab(self):
        """Вкладка логов"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Логи")
        
        # Кнопки управления логами
        log_buttons_frame = ttk.Frame(logs_frame)
        log_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_buttons_frame, text="Очистить логи", command=self._clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_buttons_frame, text="Сохранить логи", command=self._save_logs).pack(side=tk.LEFT, padx=5)
        
        # Текстовое поле для логов
        self.log_text = scrolledtext.ScrolledText(logs_frame, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def _setup_logging(self):
        """Настройка обработчика логов для GUI"""
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                try:
                    msg = self.format(record)
                    self.text_widget.config(state=tk.NORMAL)
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    self.text_widget.config(state=tk.DISABLED)
                except Exception:
                    pass
        
        if self.log_text:
            self.log_handler = GUILogHandler(self.log_text)
            self.log_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self.log_handler.setFormatter(formatter)
            
            # Добавляем обработчик к корневому логгеру
            logging.getLogger().addHandler(self.log_handler)
    
    def _start_status_updater(self):
        """Запуск обновления статуса"""
        def update_status():
            try:
                status = self.app_manager.get_status()
                
                # Обновляем статус парсинга
                if status['is_running']:
                    self.parsing_status_var.set("Запущен")
                else:
                    self.parsing_status_var.set("Остановлен")
                
                # Обновляем статус бота
                if status['telegram_bot_active']:
                    self.bot_status_var.set("Запущен")
                else:
                    self.bot_status_var.set("Не запущен")
                
                # Обновляем результаты
                if status['last_results'] and hasattr(self, 'results_text'):
                    results = status['last_results']
                    results_text = f"Последний парсинг:\n"
                    results_text += f"Успешно: {results.get('successful_products', 0)}/{results.get('total_products', 0)}\n"
                    results_text += f"URL: {results.get('category_url', 'Не указан')}\n"
                    
                    self.results_text.config(state=tk.NORMAL)
                    self.results_text.delete(1.0, tk.END)
                    self.results_text.insert(1.0, results_text)
                    self.results_text.config(state=tk.DISABLED)
                
            except Exception as e:
                logger.debug(f"Ошибка обновления статуса: {e}")
            
            # Планируем следующее обновление
            if self.root:
                self.root.after(2000, update_status)
        
        # Запускаем первое обновление
        self.root.after(1000, update_status)
    
    def _save_config(self):
        """Сохранение конфигурации"""
        try:
            # Обновляем настройки
            self.app_manager.settings.MAX_PRODUCTS = self.max_products_var.get()
            self.app_manager.settings.MAX_WORKERS = self.max_workers_var.get()
            
            messagebox.showinfo("Успех", "Настройки сохранены")
            logger.info("Настройки сохранены")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
            messagebox.showerror("Ошибка", f"Ошибка сохранения настроек: {e}")
    
    def _test_telegram(self):
        """Тест Telegram бота"""
        def test_async():
            try:
                bot_token = self.bot_token_var.get().strip()
                user_id = self.user_id_var.get().strip()
                
                if not bot_token or not user_id:
                    messagebox.showerror("Ошибка", "Заполните токен бота и User ID")
                    return
                
                success = self.app_manager.start_telegram_bot(bot_token, user_id)
                
                if success:
                    messagebox.showinfo("Успех", "Telegram бот запущен успешно!")
                else:
                    messagebox.showerror("Ошибка", "Ошибка запуска Telegram бота")
                    
            except Exception as e:
                logger.error(f"Ошибка теста Telegram: {e}")
                messagebox.showerror("Ошибка", f"Ошибка теста: {e}")
        
        threading.Thread(target=test_async, daemon=True).start()
    
    def _start_parsing(self):
        """Запуск парсинга"""
        try:
            category_url = self.category_url_var.get().strip()
            
            if not category_url:
                messagebox.showerror("Ошибка", "Укажите URL категории")
                return
            
            success = self.app_manager.start_parsing(category_url)
            
            if success:
                messagebox.showinfo("Успех", "Парсинг запущен")
            else:
                messagebox.showerror("Ошибка", "Ошибка запуска парсинга")
                
        except Exception as e:
            logger.error(f"Ошибка запуска парсинга: {e}")
            messagebox.showerror("Ошибка", f"Ошибка: {e}")
    
    def _stop_parsing(self):
        """Остановка парсинга"""
        try:
            self.app_manager.stop_parsing()
            messagebox.showinfo("Успех", "Парсинг остановлен")
        except Exception as e:
            logger.error(f"Ошибка остановки парсинга: {e}")
            messagebox.showerror("Ошибка", f"Ошибка: {e}")
    
    def _restart_parsing(self):
        """Перезапуск парсинга"""
        try:
            category_url = self.category_url_var.get().strip()
            
            if not category_url:
                messagebox.showerror("Ошибка", "Укажите URL категории")
                return
            
            success = self.app_manager.restart_parsing(category_url)
            
            if success:
                messagebox.showinfo("Успех", "Парсинг перезапущен")
            else:
                messagebox.showerror("Ошибка", "Ошибка перезапуска парсинга")
                
        except Exception as e:
            logger.error(f"Ошибка перезапуска парсинга: {e}")
            messagebox.showerror("Ошибка", f"Ошибка: {e}")
    
    def _start_bot(self):
        """Запуск Telegram бота"""
        def start_async():
            try:
                bot_token = self.bot_token_var.get().strip()
                user_id = self.user_id_var.get().strip()
                
                if not bot_token or not user_id:
                    messagebox.showerror("Ошибка", "Заполните токен бота и User ID")
                    return
                
                success = self.app_manager.start_telegram_bot(bot_token, user_id)
                
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
    
    def _clear_logs(self):
        """Очистка логов"""
        if self.log_text:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
    
    def _save_logs(self):
        """Сохранение логов"""
        try:
            from tkinter import filedialog
            
            if not self.log_text:
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                
                messagebox.showinfo("Успех", f"Логи сохранены в {filename}")
                
        except Exception as e:
            logger.error(f"Ошибка сохранения логов: {e}")
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {e}")
    
    def _on_closing(self):
        """Обработчик закрытия окна"""
        try:
            if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
                logger.info("Закрытие приложения...")
                
                # Останавливаем все процессы
                self.app_manager.shutdown()
                
                # Удаляем обработчик логов
                if self.log_handler:
                    logging.getLogger().removeHandler(self.log_handler)
                
                # Закрываем окно
                self.root.destroy()
                
        except Exception as e:
            logger.error(f"Ошибка закрытия: {e}")
            self.root.destroy()