
import logging
import threading
import time
from typing import Optional, TYPE_CHECKING
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

if TYPE_CHECKING:
    from ..core.app_manager import AppManager

logger = logging.getLogger(__name__)

class TelegramBotManager:
    
    def __init__(self, bot_token: str, user_id: str, app_manager: 'AppManager'):
        self.bot_token = bot_token
        self.user_id = user_id
        self.app_manager = app_manager
        self.application: Optional[Application] = None
        self.is_running = False
        self.bot_thread: Optional[threading.Thread] = None
        
        logger.info("Telegram бот менеджер инициализирован")
    
    def start(self) -> bool:
        try:

            self.application = Application.builder().token(self.bot_token).build()
            

            self._register_handlers()
            

            self.bot_thread = threading.Thread(target=self._run_bot, daemon=True)
            self.bot_thread.start()
            

            time.sleep(2)
            
            if self.is_running:

                self.send_message("🤖 Ozon Parser бот запущен и готов к работе!")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Ошибка запуска Telegram бота: {e}")
            return False
    
    def _run_bot(self):
        try:
            self.is_running = True
            logger.info("Telegram бот запущен")
            

            self.application.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            logger.error(f"Ошибка работы Telegram бота: {e}")
        finally:
            self.is_running = False
    
    def _register_handlers(self):

        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("status", self._cmd_status))
        self.application.add_handler(CommandHandler("stop", self._cmd_stop))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        

        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized_user(update):
            return
        
        welcome_text = (
            "🤖 Добро пожаловать в Ozon Parser!\n\n"
            "Доступные команды:\n"
            "/status - статус парсера\n"
            "/stop - остановить парсинг\n"
            "/help - помощь\n\n"
            "Отправьте ссылку на категорию Ozon для начала парсинга"
        )
        
        await update.message.reply_text(welcome_text)
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized_user(update):
            return
        
        status = self.app_manager.get_status()
        
        status_text = f"📊 Статус парсера:\n\n"
        status_text += f"🔄 Парсинг активен: {'Да' if status['is_running'] else 'Нет'}\n"
        status_text += f"🤖 Telegram бот: {'Активен' if status['telegram_bot_active'] else 'Неактивен'}\n"
        status_text += f"📦 Макс. товаров: {status['settings']['max_products']}\n"
        status_text += f"👥 Макс. воркеров: {status['settings']['max_workers']}\n"
        
        if status['last_results']:
            results = status['last_results']
            status_text += f"\n📈 Последний результат:\n"
            status_text += f"Успешно: {results.get('successful_products', 0)}/{results.get('total_products', 0)}"
        
        await update.message.reply_text(status_text)
    
    async def _cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized_user(update):
            return
        
        if self.app_manager.is_running:
            self.app_manager.stop_parsing()
            await update.message.reply_text("⏹️ Парсинг остановлен")
        else:
            await update.message.reply_text("ℹ️ Парсинг не запущен")
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized_user(update):
            return
        
        help_text = (
            "🆘 Помощь по использованию:\n\n"
            "1. Отправьте ссылку на категорию Ozon для начала парсинга\n"
            "2. Используйте /status для проверки статуса\n"
            "3. Используйте /stop для остановки парсинга\n\n"
            "Пример ссылки:\n"
            "https://ozon.ru/category/sistemnye-bloki-15704/\n\n"
            "Бот будет уведомлять вас о ходе парсинга"
        )
        
        await update.message.reply_text(help_text)
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized_user(update):
            return
        
        message_text = update.message.text.strip()
        

        if self._is_ozon_category_url(message_text):
            if self.app_manager.is_running:
                await update.message.reply_text("⚠️ Парсинг уже запущен. Дождитесь завершения или остановите его командой /stop")
                return
            
            await update.message.reply_text("🚀 Запускаю парсинг...")
            success = self.app_manager.start_parsing(message_text)
            
            if not success:
                await update.message.reply_text("❌ Ошибка запуска парсинга")
        else:
            await update.message.reply_text(
                "❓ Не понимаю команду. Отправьте ссылку на категорию Ozon или используйте /help"
            )
    
    def _is_authorized_user(self, update: Update) -> bool:
        user_id = str(update.effective_user.id)
        if user_id != self.user_id:
            logger.warning(f"Неавторизованный доступ от пользователя {user_id}")
            return False
        return True
    
    def _is_ozon_category_url(self, url: str) -> bool:
        return (
            url.startswith(('http://', 'https://')) and
            'ozon.ru' in url and
            '/category/' in url
        )
    
    def send_message(self, text: str) -> bool:
        try:
            if not self.is_running or not self.application:
                return False
            

            bot = Bot(token=self.bot_token)
            

            def send_async():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(bot.send_message(chat_id=self.user_id, text=text))
                    loop.close()
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения: {e}")
            
            thread = threading.Thread(target=send_async, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в Telegram: {e}")
            return False
    
    def stop(self):
        try:
            self.is_running = False
            
            if self.application:
    
                if hasattr(self.application, 'stop'):
                    self.application.stop()
                
                if hasattr(self.application, 'shutdown'):
                    self.application.shutdown()
            

            if self.bot_thread and self.bot_thread.is_alive():
                self.bot_thread.join(timeout=5)
            
            logger.info("Telegram бот остановлен")
            
        except Exception as e:
            logger.error(f"Ошибка остановки Telegram бота: {e}")