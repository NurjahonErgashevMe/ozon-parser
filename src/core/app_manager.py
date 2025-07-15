
import logging
import threading
from typing import Dict, Any, List
from ..config.settings import Settings
from ..parsers.link_parser import OzonLinkParser
from ..parsers.product_parser import OzonProductParser
from ..parsers.seller_parser import OzonSellerParser

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
        
        # Этап 3: Парсинг данных продавцов
        logger.info("Этап 3: Парсинг данных продавцов")
        
        # Собираем уникальные seller_id из результатов товаров
        seller_ids = []
        for product in product_results:
            if product.seller_id and product.success:
                seller_ids.append(product.seller_id)
        
        unique_seller_ids = list(set(seller_ids))
        logger.info(f"Найдено {len(unique_seller_ids)} уникальных продавцов для парсинга")
        
        seller_results = []
        if unique_seller_ids:
            seller_parser = OzonSellerParser(self.settings.MAX_WORKERS)
            seller_results = seller_parser.parse_sellers(unique_seller_ids)
        
        if self.stop_event.is_set():
            logger.info("Парсинг прерван пользователем")
            return
        
        # Создаем словарь для быстрого доступа к данным продавцов
        seller_data = {}
        for seller in seller_results:
            if seller.success:
                seller_data[seller.seller_id] = seller
        
        self.last_results = {
            'links': product_links,
            'products': product_results,
            'sellers': seller_results,
            'category_url': category_url,
            'total_products': len(product_results),
            'successful_products': len([p for p in product_results if p.success]),
            'total_sellers': len(seller_results),
            'successful_sellers': len([s for s in seller_results if s.success]),
            'output_folder': getattr(link_parser, 'output_folder', 'unknown'),
            'seller_data': seller_data
        }
        
        self._save_results_to_file()
        
        success_count = self.last_results['successful_products']
        total_count = self.last_results['total_products']
        seller_success_count = self.last_results['successful_sellers']
        seller_total_count = self.last_results['total_sellers']
        
        logger.info(f"Парсинг завершен: {success_count}/{total_count} товаров и {seller_success_count}/{seller_total_count} продавцов обработано успешно")
    
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
                'total_sellers': self.last_results.get('total_sellers', 0),
                'successful_sellers': self.last_results.get('successful_sellers', 0),
                'products': []
            }
            
            for product in self.last_results.get('products', []):
                product_url = ""
                for url in self.last_results.get('links', {}).keys():
                    if product.article in url:
                        product_url = url
                        break
                
                # Получаем данные продавца, если есть
                seller_info = self.last_results.get('seller_data', {}).get(product.seller_id, None)
                
                seller_data = {
                    'name': product.company_name,
                    'id': product.seller_id,
                    'link': product.seller_link,
                    'inn': '',
                    'company_name': ''
                }
                
                # Если есть данные продавца, добавляем их
                if seller_info:
                    # Заменяем кавычки на обычные
                    company_name = seller_info.company_name.replace('\\"', '"').replace('\"', '"').replace('"', '"')
                    
                    seller_data.update({
                        'inn': seller_info.inn,
                        'company_name': company_name,
                        'orders_count': seller_info.orders_count,
                        'reviews_count': seller_info.reviews_count,
                        'working_time': seller_info.working_time,
                        'average_rating': seller_info.average_rating
                    })
                
                # Заменяем кавычки в названии компании
                if 'name' in seller_data:
                    seller_data['name'] = seller_data['name'].replace('\\"', '"').replace('\"', '"').replace('"', '"')
                
                save_data['products'].append({
                    'article': product.article,
                    'name': product.name,
                    'seller': seller_data,
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