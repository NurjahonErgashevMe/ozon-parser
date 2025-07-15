
import logging
import time
import json
import re
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from typing import Dict, List, Tuple
from ..utils.selenium_manager import SeleniumManager

logger = logging.getLogger(__name__)

class OzonLinkParser:
    
    def __init__(self, category_url: str, max_products: int = 100):
        self.category_url = category_url
        self.max_products = max_products
        self.selenium_manager = SeleniumManager()
        self.driver = None
        self.collected_links = {}  # {url: image_url}
        
        # Извлекаем название категории и создаем timestamp
        self.category_name = self._extract_category_name(category_url)
        self.timestamp = datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
        self.output_folder = f"{self.category_name}_{self.timestamp}"
        
        logger.info(f"Инициализирован парсер для категории: {self.category_name}")
    
    def _extract_category_name(self, url: str) -> str:
        try:
            # Ищем паттерн /category/название-категории-id/
            match = re.search(r'/category/([^/]+)-(\d+)/', url)
            if match:
                category_name = match.group(1).replace('-', '_')
                return category_name
            return "unknown_category"
        except Exception:
            return "unknown_category"
    
    def start_parsing(self) -> Tuple[bool, Dict[str, str]]:
        try:
            logger.info(f"Начало парсинга ссылок для {self.max_products} товаров")
            
            # Создаем папку сразу
            self._create_output_folder()
            
            # Создаем драйвер
            self.driver = self.selenium_manager.create_driver()
            
            # Загружаем страницу
            if not self._load_page():
                return False, {}
            
            # Собираем ссылки
            self._collect_links()
            
            # Сохраняем результат
            success = self._save_links()
            
            logger.info(f"Парсинг завершен. Собрано {len(self.collected_links)} ссылок")
            return success, self.collected_links
            
        except Exception as e:
            logger.error(f"Ошибка парсинга ссылок: {e}")
            return False, {}
        finally:
            self._cleanup()
    
    def _load_page(self) -> bool:
        try:
            logger.info(f"Загрузка страницы: {self.category_url}")
            
            if not self.selenium_manager.navigate_to_url(self.category_url):
                logger.error("Не удалось загрузить страницу")
                return False
            
            # Ждем загрузки контейнера с товарами с увеличенным таймаутом
            logger.info("Ожидание загрузки контейнера товаров...")
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "contentScrollPaginator"))
            )
            
            logger.info("Страница загружена успешно")
            return True
            
        except TimeoutException:
            logger.error("Таймаут загрузки страницы - контейнер товаров не найден")
            return False
        except Exception as e:
            logger.error(f"Ошибка загрузки страницы: {e}")
            return False
    
    def _collect_links(self):
        unique_links = set()
        ordered_links = []
        
        # Первичный сбор
        current_links = self._extract_all_links()
        new_links = set(current_links.keys()) - unique_links
        
        if new_links:
            for link in new_links:
                unique_links.add(link)
                ordered_links.append(link)
                self.collected_links[link] = current_links[link]
        
        # Продолжаем до набора нужного количества
        while len(ordered_links) < self.max_products:
            self._scroll_to_bottom()
            
            current_links = self._extract_all_links()
            new_links = set(current_links.keys()) - unique_links
            
            if new_links:
                logger.info(f"Найдено новых ссылок: {len(new_links)}")
                for link in new_links:
                    unique_links.add(link)
                    ordered_links.append(link)
                    self.collected_links[link] = current_links[link]
                    if len(ordered_links) >= self.max_products:
                        break
                logger.info(f"Собрано: {len(ordered_links)}/{self.max_products}")
            
            time.sleep(0.5)
    
    def _extract_all_links(self) -> Dict[str, str]:
        try:
            # Перенаходим контейнер каждый раз чтобы избежать stale element
            container = self.driver.find_element(By.ID, "contentScrollPaginator")
            elements = container.find_elements(By.CSS_SELECTOR, "div[data-index]")
            
            links_with_images = {}
            
            for element in elements:
                try:
                    # Получаем атрибуты сразу, не сохраняя ссылки на элементы
                    data_index = element.get_attribute("data-index")
                    
                    link_element = element.find_element(By.CSS_SELECTOR, "a.tile-clickable-element")
                    href = link_element.get_attribute("href")
                    
                    img_element = element.find_element(By.CSS_SELECTOR, "img")
                    img_url = img_element.get_attribute("src")
                    
                    if href and href.startswith("https://www.ozon.ru/product/") and img_url:
                        links_with_images[href] = img_url
                        
                except Exception:
                    continue
                
            return links_with_images
            
        except Exception as e:
            logger.warning(f"Ошибка извлечения ссылок: {e}")
            return {}
    
    def _scroll_to_bottom(self):
        try:
            last_seen_index = -1
            
            while True:
                # Перенаходим элементы каждый раз
                container = self.driver.find_element(By.ID, "contentScrollPaginator")
                items = container.find_elements(By.CSS_SELECTOR, "div[data-index]")
                
                if not items:
                    break
                    
                current_last_index = int(items[-1].get_attribute("data-index"))
                
                if current_last_index == last_seen_index:
                    break
                    
                last_seen_index = current_last_index
                
                # Используем JavaScript для скролла вместо ссылки на элемент
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
                
        except Exception as e:
            logger.debug(f"Ошибка скролла: {e}")
    

    
    def _create_output_folder(self):
        from pathlib import Path
        base_output_dir = Path(__file__).parent.parent.parent / "output"
        self.output_dir = base_output_dir / self.output_folder
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Создана папка: {self.output_dir}")
    
    def _save_links(self) -> bool:
        try:
            filename = f"links_{self.output_folder}.json"
            file_path = self.output_dir / filename
            
            links_to_save = dict(list(self.collected_links.items())[:self.max_products])
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(links_to_save, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Ссылки сохранены в JSON: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения ссылок: {e}")
            return False
    
    def _cleanup(self):
        if self.selenium_manager:
            self.selenium_manager.close()
    
    def get_article_from_url(self, url: str) -> str:
        try:
            # Паттерн для извлечения артикула из URL
            # https://www.ozon.ru/product/название-товара-916479391/
            match = re.search(r'/product/[^/]+-(\d+)/', url)
            if match:
                return match.group(1)
            return ""
        except Exception:
            return ""