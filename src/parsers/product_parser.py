
import logging
import json
import re
import time
import concurrent.futures
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from ..utils.selenium_manager import SeleniumManager

logger = logging.getLogger(__name__)

@dataclass
class ProductInfo:
    article: str
    name: str = ""
    company_name: str = ""
    company_inn: str = ""
    image_url: str = ""
    card_price: int = 0
    price: int = 0
    original_price: int = 0
    seller_id: str = ""
    seller_link: str = ""
    success: bool = False
    error: str = ""

class ProductWorker:
    
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.selenium_manager = SeleniumManager()
        self.driver = None
        logger.info(f"Воркер {worker_id} инициализирован")
    
    def initialize(self):
        try:
            self.driver = self.selenium_manager.create_driver()
            logger.info(f"Воркер {self.worker_id} готов к работе")
        except Exception as e:
            logger.error(f"Ошибка инициализации воркера {self.worker_id}: {e}")
            raise
    
    def parse_products(self, articles: List[str], product_links: Dict[str, str]) -> List[ProductInfo]:
        results = []
        
        for article in articles:
            try:
                # Находим ссылку и изображение для артикула
                product_url = ""
                image_from_links = ""
                
                for url, img_url in product_links.items():
                    if article in url:
                        product_url = url
                        image_from_links = img_url
                        break
                
                result = self._parse_single_product(article)
                
                # Используем изображение из ссылок вместо API
                if result.success and image_from_links:
                    result.image_url = image_from_links
                
                results.append(result)
                
                if result.success:
                    logger.info(f"Воркер {self.worker_id}: Товар {article} обработан успешно")
                else:
                    logger.warning(f"Воркер {self.worker_id}: Ошибка товара {article}: {result.error}")
                    
            except Exception as e:
                logger.error(f"Воркер {self.worker_id}: Критическая ошибка товара {article}: {e}")
                results.append(ProductInfo(article=article, error=str(e)))
            
            time.sleep(0.5)
        
        return results
    
    def _parse_single_product(self, article: str) -> ProductInfo:
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Строим URL для API
                api_url = f"https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=/product/{article}&__rr=1"
                
                # Переходим на страницу API
                if not self.selenium_manager.navigate_to_url(api_url):
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return ProductInfo(article=article, error="Не удалось загрузить страницу API")
                
                # Ждем JSON ответ
                json_content = self.selenium_manager.wait_for_json_response(timeout=15)
                
                if not json_content:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return ProductInfo(article=article, error="Не получен JSON ответ")
                
                # Парсим JSON
                product_info = self._parse_json_response(article, json_content)
                
                if product_info.success:
                    return product_info
                elif attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    return product_info
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.debug(f"Попытка {attempt + 1} неудачна для товара {article}: {e}")
                    time.sleep(2)
                    continue
                else:
                    return ProductInfo(article=article, error=f"Ошибка парсинга: {str(e)}")
        
        return ProductInfo(article=article, error="Превышено количество попыток")
    
    def _parse_json_response(self, article: str, json_content: str) -> ProductInfo:
        try:
            data = json.loads(json_content)
            
            if 'widgetStates' not in data:
                return ProductInfo(article=article, error="Отсутствует widgetStates в ответе")
            
            widget_states = data['widgetStates']
            product_info = ProductInfo(article=article)
            
            # Ищем информацию о товаре в webStickyProducts
            sticky_product_data = self._find_sticky_product_data(widget_states)
            if sticky_product_data:
                product_info.name = sticky_product_data.get('name', '')
                product_info.image_url = sticky_product_data.get('coverImageUrl', '')
                
                # Информация о продавце
                seller_info = sticky_product_data.get('seller', {})
                product_info.company_name = seller_info.get('name', '')
                product_info.company_inn = seller_info.get('inn', '')
                
                # Извлекаем ID и ссылку продавца
                seller_link = seller_info.get('link', '')
                if seller_link:
                    seller_id = re.search(r'/seller/(\d+)/', seller_link)
                    if seller_id:
                        product_info.seller_id = seller_id.group(1)
                        product_info.seller_link = f"https://ozon.ru/seller/{seller_id.group(1)}"
            
            # Ищем информацию о ценах в webPrice
            price_data = self._find_price_data(widget_states)
            if price_data:
                product_info.card_price = self._extract_price_number(price_data.get('cardPrice', ''))
                product_info.price = self._extract_price_number(price_data.get('price', ''))
                product_info.original_price = self._extract_price_number(price_data.get('originalPrice', ''))
            
            # Проверяем, что получили основную информацию
            if product_info.name or product_info.card_price:
                product_info.success = True
            else:
                product_info.error = "Не найдена основная информация о товаре"
            
            return product_info
            
        except json.JSONDecodeError as e:
            return ProductInfo(article=article, error=f"Ошибка парсинга JSON: {str(e)}")
        except Exception as e:
            return ProductInfo(article=article, error=f"Ошибка обработки данных: {str(e)}")
    
    def _find_sticky_product_data(self, widget_states: Dict) -> Optional[Dict]:
        for key, value in widget_states.items():
            if key.startswith('webStickyProducts-') and isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    continue
        return None
    
    def _find_price_data(self, widget_states: Dict) -> Optional[Dict]:
        for key, value in widget_states.items():
            if key.startswith('webPrice-') and isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    continue
        return None
    
    def _extract_price_number(self, price_str: str) -> int:
        if not price_str:
            return 0
        try:
            cleaned = re.sub(r'[^\d]', '', str(price_str))
            return int(cleaned) if cleaned else 0
        except:
            return 0
    
    def close(self):
        if self.selenium_manager:
            self.selenium_manager.close()
        logger.info(f"Воркер {self.worker_id} закрыт")

class OzonProductParser:
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.results: List[ProductInfo] = []
        logger.info(f"Парсер товаров инициализирован с {max_workers} воркерами")
    
    def parse_products(self, product_links: Dict[str, str]) -> List[ProductInfo]:
        # Сохраняем ссылки для использования в воркерах
        self.product_links = product_links
        
        articles = []
        for url in product_links.keys():
            article = self._extract_article_from_url(url)
            if article:
                articles.append(article)
        
        if not articles:
            logger.error("Не найдено артикулов для парсинга")
            return []
        
        optimal_workers = self._calculate_optimal_workers(len(articles))
        
        logger.info(f"Начало парсинга {len(articles)} товаров с {optimal_workers} воркерами")
        
        if optimal_workers == 1:
            return self._parse_single_worker(articles)
        else:
            return self._parse_multiple_workers(articles, optimal_workers)
    
    def _extract_article_from_url(self, url: str) -> str:
        try:
            match = re.search(r'/product/[^/]+-(\d+)/', url)
            return match.group(1) if match else ""
        except Exception:
            return ""
    
    def _parse_single_worker(self, articles: List[str]) -> List[ProductInfo]:
        worker = ProductWorker(1)
        try:
            worker.initialize()
            return worker.parse_products(articles, self.product_links)
        finally:
            worker.close()
    
    def _calculate_optimal_workers(self, total_links: int) -> int:
        if total_links <= 10:
            return 1
        elif total_links <= 25:
            return 2
        elif total_links <= 50:
            return 3
        elif total_links <= 75:
            return 4
        else:
            return min(5, self.max_workers)
    
    def _parse_multiple_workers(self, articles: List[str], num_workers: int) -> List[ProductInfo]:
        chunks = self._distribute_articles(articles, num_workers)
        
        # Логируем распределение
        for i, chunk in enumerate(chunks):
            if chunk:
                logger.info(f"Воркер {i+1}: {len(chunk)} товаров")
        
        all_results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            future_to_worker = {}
            
            for i, chunk in enumerate(chunks):
                if chunk:
                    future = executor.submit(self._worker_task_with_retry, i + 1, chunk)
                    future_to_worker[future] = i + 1
            
            for future in concurrent.futures.as_completed(future_to_worker):
                worker_id = future_to_worker[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                    logger.info(f"Воркер {worker_id} завершил работу с {len(results)} товарами")
                except Exception as e:
                    logger.error(f"Ошибка воркера {worker_id}: {e}")
        
        return self._sort_results_by_original_order(all_results, articles)
    
    def _distribute_articles(self, articles: List[str], num_workers: int) -> List[List[str]]:
        chunks = [[] for _ in range(num_workers)]
        
        for i, article in enumerate(articles):
            worker_index = i % num_workers
            chunks[worker_index].append(article)
        
        return chunks
    
    def _worker_task_with_retry(self, worker_id: int, articles: List[str]) -> List[ProductInfo]:
        max_worker_retries = 3
        for attempt in range(max_worker_retries):
            worker = ProductWorker(worker_id)
            try:
                worker.initialize()
                return worker.parse_products(articles, self.product_links)
            except Exception as e:
                worker.close()
                if "Access blocked" in str(e) and attempt < max_worker_retries - 1:
                    logger.warning(
                        f"Воркер {worker_id} заблокирован, пересоздаем (попытка {attempt + 1}/3)"
                    )
                    time.sleep(10)     
                    continue
                else:
                    raise
        return []
    
    def _sort_results_by_original_order(self, results: List[ProductInfo], original_articles: List[str]) -> List[ProductInfo]:
        result_dict = {result.article: result for result in results}
        return [result_dict.get(article, ProductInfo(article=article, error="Не обработан")) 
                for article in original_articles]