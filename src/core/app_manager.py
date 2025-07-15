
import logging
import threading
from typing import Dict, Any
from ..config.settings import Settings
from ..parsers.link_parser import OzonLinkParser
from ..parsers.product_parser import OzonProductParser

logger = logging.getLogger(__name__)

class AppManager:
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.is_running = False
        self.stop_event = threading.Event()
        self.last_results = {}
        
        logger.info("Менеджер приложения инициализирован")
    
    def start_parsing(self, category_url: str) -> bool:
        if self.is_running:
            logger.warning("Парсинг уже запущен")
            return False
        
        try:
            self.stop_event.clear()
            self.is_running = True
            self._parsing_task(category_url)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска парсинга: {e}")
            return False
        finally:
            self.is_running = False
    
    def stop_parsing(self):
        logger.info("Остановка парсинга...")
        self.stop_event.set()
        self.is_running = False
    
    def _parsing_task(self, category_url: str):
        logger.info(f"Начало парсинга категории: {category_url}")
        
        logger.info("Этап 1: Сбор ссылок товаров")
        link_parser = OzonLinkParser(category_url, self.settings.MAX_PRODUCTS)
        
        success, product_links = link_parser.start_parsing()
        
        if self.stop_event.is_set():
            logger.info("Парсинг прерван пользователем")
            return
        
        if not success or not product_links:
            logger.error("Не удалось собрать ссылки товаров")
            return
        
        logger.info(f"Собрано {len(product_links)} ссылок товаров")
        
        if self.stop_event.is_set():
            return
        
        logger.info("Этап 2: Парсинг данных товаров")
        product_parser = OzonProductParser(self.settings.MAX_WORKERS)
        product_results = product_parser.parse_products(product_links)
        
        if self.stop_event.is_set():
            logger.info("Парсинг прерван пользователем")
            return
        

        self.last_results = {
            'links': product_links,
            'products': product_results,
            'category_url': category_url,
            'total_products': len(product_results),
            'successful_products': len([p for p in product_results if p.success]),
            'output_folder': getattr(link_parser, 'output_folder', 'unknown')
        }
        
        self._save_results_to_file()
        

        success_count = self.last_results['successful_products']
        total_count = self.last_results['total_products']
        
        logger.info(f"Парсинг завершен: {success_count}/{total_count} товаров обработано успешно")
    
    def _save_results_to_file(self):
        try:
            import json
            from datetime import datetime
            from pathlib import Path
            
            folder_name = self.last_results.get('output_folder', 'unknown')
            filename = f"category_{folder_name}.json"
            current_timestamp = datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
            
            output_dir = self.settings.OUTPUT_DIR / folder_name
            filepath = output_dir / filename
            
            save_data = {
                'timestamp': current_timestamp,
                'category_url': self.last_results.get('category_url', ''),
                'total_products': self.last_results.get('total_products', 0),
                'successful_products': self.last_results.get('successful_products', 0),
                'products': []
            }
            
            for product in self.last_results.get('products', []):
                product_url = ""
                for url in self.last_results.get('links', {}).keys():
                    if product.article in url:
                        product_url = url
                        break
                
                save_data['products'].append({
                    'article': product.article,
                    'name': product.name,
                    'company_name': product.company_name,
                    'image_url': product.image_url,
                    'card_price': product.card_price,
                    'price': product.price,
                    'original_price': product.original_price,
                    'product_url': product_url,
                    'success': product.success,
                    'error': product.error
                })
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Результаты сохранены в файл: {filepath}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения результатов: {e}")
    
    def shutdown(self):
        logger.info("Завершение работы приложения...")
        self.stop_parsing()
        logger.info("Приложение завершено")