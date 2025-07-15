import logging
import json
import re
import time
import concurrent.futures
import html
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from ..utils.selenium_manager import SeleniumManager

logger = logging.getLogger(__name__)

@dataclass
class SellerInfo:
    seller_id: str
    company_name: str = ""
    inn: str = ""
    orders_count: str = ""
    reviews_count: str = ""
    working_time: str = ""
    average_rating: str = ""
    success: bool = False
    error: str = ""

class SellerWorker:
    
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.selenium_manager = SeleniumManager()
        self.driver = None
        logger.info(f"Воркер продавцов {worker_id} инициализирован")
    
    def initialize(self):
        try:
            self.driver = self.selenium_manager.create_driver()
            logger.info(f"Воркер продавцов {self.worker_id} готов к работе")
        except Exception as e:
            logger.error(f"Ошибка инициализации воркера продавцов {self.worker_id}: {e}")
            raise
    
    def parse_sellers(self, seller_ids: List[str]) -> List[SellerInfo]:
        results = []
        
        for seller_id in seller_ids:
            try:
                result = self._parse_single_seller(seller_id)
                results.append(result)
                
                if result.success:
                    logger.info(f"Воркер {self.worker_id}: Продавец {seller_id} обработан успешно")
                else:
                    logger.warning(f"Воркер {self.worker_id}: Ошибка продавца {seller_id}: {result.error}")
                    
            except Exception as e:
                logger.error(f"Воркер {self.worker_id}: Критическая ошибка продавца {seller_id}: {e}")
                results.append(SellerInfo(seller_id=seller_id, error=str(e)))
            
            time.sleep(0.5)
        
        return results
    
    def _parse_single_seller(self, seller_id: str) -> SellerInfo:
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Строим URL для API
                api_url = f"https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=/modal/shop-in-shop-info?seller_id={seller_id}&__rr=1"
                
                # Переходим на страницу API
                if not self.selenium_manager.navigate_to_url(api_url):
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return SellerInfo(seller_id=seller_id, error="Не удалось загрузить страницу API")
                
                # Ждем JSON ответ
                json_content = self.selenium_manager.wait_for_json_response(timeout=15)
                
                if not json_content:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return SellerInfo(seller_id=seller_id, error="Не получен JSON ответ")
                
                # Парсим JSON
                seller_info = self._parse_json_response(seller_id, json_content)
                
                if seller_info.success:
                    return seller_info
                elif attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    return seller_info
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.debug(f"Попытка {attempt + 1} неудачна для продавца {seller_id}: {e}")
                    time.sleep(2)
                    continue
                else:
                    return SellerInfo(seller_id=seller_id, error=f"Ошибка парсинга: {str(e)}")
        
        return SellerInfo(seller_id=seller_id, error="Превышено количество попыток")
    
    def _parse_json_response(self, seller_id: str, json_content: str) -> SellerInfo:
        try:
            data = json.loads(json_content)
            
            if 'widgetStates' not in data:
                return SellerInfo(seller_id=seller_id, error="Отсутствует widgetStates в ответе")
            
            widget_states = data['widgetStates']
            seller_info = SellerInfo(seller_id=seller_id)
            
            # Ищем все textBlock ключи в widgetStates
            for key, value in widget_states.items():
                if key.startswith('textBlock-') and isinstance(value, str):
                    company_data = self._extract_company_data(value)
                    if company_data[0] or company_data[1]:  # Если нашли хоть что-то
                        seller_info.company_name = company_data[0]
                        seller_info.inn = company_data[1]
                        break
            
            # Ищем все cellList ключи в widgetStates
            for key, value in widget_states.items():
                if key.startswith('cellList-') and isinstance(value, str):
                    cell_data = self._extract_cell_list_data(value)
                    if any(cell_data.values()):  # Если нашли хоть какие-то данные
                        seller_info.orders_count = cell_data.get("orders", "")
                        seller_info.working_time = cell_data.get("working_time", "")
                        seller_info.average_rating = cell_data.get("rating", "")
                        seller_info.reviews_count = cell_data.get("reviews", "")
                        break
            
            # Проверяем, что получили основную информацию
            if seller_info.company_name or seller_info.inn or seller_info.orders_count or seller_info.reviews_count:
                seller_info.success = True
            else:
                seller_info.error = "Не найдена основная информация о продавце"
            
            return seller_info
            
        except json.JSONDecodeError as e:
            return SellerInfo(seller_id=seller_id, error=f"Ошибка парсинга JSON: {str(e)}")
        except Exception as e:
            return SellerInfo(seller_id=seller_id, error=f"Ошибка обработки данных: {str(e)}")
    

    
    def _extract_company_data(self, text_block_data: str) -> tuple:
        """Извлекает название компании и ИНН из textBlock"""
        try:
            data = json.loads(text_block_data)
            if "body" in data and isinstance(data["body"], list):
                full_text = ""
                
                # Собираем текст из textAtom
                for item in data["body"]:
                    if "textAtom" in item and "text" in item["textAtom"]:
                        text = item["textAtom"]["text"]
                        full_text += text + "\n"
                
                # Ищем ИНН (последовательность цифр в конце)
                inn_match = re.search(r'\d{10,15}', full_text)
                if inn_match:
                    inn = inn_match.group(0)
                    
                    # Разбиваем по <br> и берем первую часть как название компании
                    parts = full_text.split('&lt;br&gt;')
                    if parts:
                        company_name = parts[0].strip()
                        # Декодируем HTML-сущности
                        company_name = html.unescape(company_name)
                        return company_name, inn
                
                return "", ""
            
            return "", ""
        except Exception as e:
            return "", ""
    
    def _extract_cell_list_data(self, cell_list_data: str) -> Dict[str, str]:
        """Извлекает данные о продавце из cellList"""
        result = {
            "orders": "",
            "working_time": "",
            "rating": "",
            "reviews": ""
        }
        
        try:
            data = json.loads(cell_list_data)
            if "cells" in data and isinstance(data["cells"], list):
                for cell in data["cells"]:
                    if "dsCell" not in cell:
                        continue
                    
                    ds_cell = cell["dsCell"]
                    if "centerBlock" not in ds_cell or "rightBlock" not in ds_cell:
                        continue
                    
                    # Получаем заголовок ячейки
                    title = ""
                    if "title" in ds_cell["centerBlock"] and "text" in ds_cell["centerBlock"]["title"]:
                        title = ds_cell["centerBlock"]["title"]["text"].lower()
                    
                    # Получаем значение ячейки
                    value = ""
                    if "badge" in ds_cell["rightBlock"] and "text" in ds_cell["rightBlock"]["badge"]:
                        value = ds_cell["rightBlock"]["badge"]["text"]
                    
                    # Заполняем соответствующие поля
                    if "заказов" in title:
                        result["orders"] = value
                    elif "работает с ozon" in title:
                        result["working_time"] = value
                    elif "средняя оценка" in title:
                        result["rating"] = value
                    elif "количество отзывов" in title:
                        result["reviews"] = value
            
            return result
        except:
            return result
    
    def close(self):
        if self.selenium_manager:
            self.selenium_manager.close()
        logger.info(f"Воркер продавцов {self.worker_id} закрыт")

class OzonSellerParser:
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        logger.info(f"Парсер продавцов инициализирован с {max_workers} воркерами")
    
    def parse_sellers(self, seller_ids: List[str]) -> List[SellerInfo]:
        # Удаляем дубликаты seller_ids
        unique_seller_ids = list(set(seller_ids))
        
        if not unique_seller_ids:
            logger.error("Не найдено ID продавцов для парсинга")
            return []
        
        optimal_workers = self._calculate_optimal_workers(len(unique_seller_ids))
        
        logger.info(f"Начало парсинга {len(unique_seller_ids)} продавцов с {optimal_workers} воркерами")
        
        if optimal_workers == 1:
            return self._parse_single_worker(unique_seller_ids)
        else:
            return self._parse_multiple_workers(unique_seller_ids, optimal_workers)
    
    def _parse_single_worker(self, seller_ids: List[str]) -> List[SellerInfo]:
        worker = SellerWorker(1)
        try:
            worker.initialize()
            return worker.parse_sellers(seller_ids)
        finally:
            worker.close()
    
    def _calculate_optimal_workers(self, total_sellers: int) -> int:
        if total_sellers <= 10:
            return 1
        elif total_sellers <= 25:
            return 2
        elif total_sellers <= 50:
            return 3
        elif total_sellers <= 75:
            return 4
        else:
            return min(5, self.max_workers)
    
    def _parse_multiple_workers(self, seller_ids: List[str], num_workers: int) -> List[SellerInfo]:
        chunks = self._distribute_seller_ids(seller_ids, num_workers)
        
        # Логируем распределение
        for i, chunk in enumerate(chunks):
            if chunk:
                logger.info(f"Воркер продавцов {i+1}: {len(chunk)} продавцов")
        
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
                    logger.info(f"Воркер продавцов {worker_id} завершил работу с {len(results)} продавцами")
                except Exception as e:
                    logger.error(f"Ошибка воркера продавцов {worker_id}: {e}")
        
        return all_results
    
    def _distribute_seller_ids(self, seller_ids: List[str], num_workers: int) -> List[List[str]]:
        chunks = [[] for _ in range(num_workers)]
        
        for i, seller_id in enumerate(seller_ids):
            worker_index = i % num_workers
            chunks[worker_index].append(seller_id)
        
        return chunks
    
    def _worker_task_with_retry(self, worker_id: int, seller_ids: List[str]) -> List[SellerInfo]:
        max_worker_retries = 3
        
        for attempt in range(max_worker_retries):
            worker = SellerWorker(worker_id)
            try:
                worker.initialize()
                return worker.parse_sellers(seller_ids)
            except Exception as e:
                worker.close()
                if "Access blocked" in str(e) and attempt < max_worker_retries - 1:
                    logger.warning(f"Воркер продавцов {worker_id} заблокирован, пересоздаем (попытка {attempt + 1})")
                    time.sleep(5)
                    continue
                else:
                    raise
        
        return []