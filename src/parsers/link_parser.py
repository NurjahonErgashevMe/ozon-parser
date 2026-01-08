import logging
import time
import json
import re
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from typing import Dict, Tuple
from ..utils.selenium_manager import SeleniumManager
from ..utils.resource_manager import resource_manager

logger = logging.getLogger(__name__)

class OzonLinkParser:
    
    def __init__(self, category_url: str, max_products: int = 100, user_id: str = None):
        self.category_url = category_url
        self.max_products = max_products
        self.user_id = user_id
        self.selenium_manager = SeleniumManager()
        self.driver = None
        self.collected_links = {}
        
        self.category_name = self._extract_category_name(category_url)
        self.timestamp = datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
        self.output_folder = f"{self.category_name}_{self.timestamp}"
    
    def _extract_category_name(self, url: str) -> str:
        try:
            match = re.search(r'/category/([^/]+)-(\d+)/', url)
            if match:
                return match.group(1).replace('-', '_')
            if '/search/' in url:
                return "search"
            return "unknown_category"
        except Exception:
            return "unknown_category"
    
    def start_parsing(self) -> Tuple[bool, Dict[str, str]]:
        try:
            # Регистрируем сессию парсинга ссылок
            if self.user_id:
                resource_manager.start_parsing_session(self.user_id, 'links', self.max_products)
            
            self._create_output_folder()
            self.driver = self.selenium_manager.create_driver()
            
            if not self._load_page():
                return False, {}
            
            self._collect_links()
            success = self._save_links()
            
            logger.info(f"Собрано {len(self.collected_links)} ссылок для пользователя {self.user_id}")
            return success, self.collected_links
            
        except Exception as e:
            logger.error(f"Ошибка парсинга ссылок: {e}")
            return False, {}
        finally:
            self._cleanup()
            # Завершаем сессию парсинга ссылок
            if self.user_id:
                resource_manager.finish_parsing_session(self.user_id)
    
    def _load_page(self) -> bool:
        max_driver_retries = 3  # Максимум 3 драйвера
        
        for driver_attempt in range(max_driver_retries):
            try:
                logger.info(f"Попытка загрузки страницы с драйвером #{driver_attempt + 1}/{max_driver_retries}")
                
                # Если это не первая попытка - пересоздаем драйвер
                if driver_attempt > 0:
                    logger.info(f"Пересоздание драйвера после блокировки (драйвер #{driver_attempt + 1})")
                    self.selenium_manager.close()
                    time.sleep(3)  # Пауза перед созданием нового драйвера
                    self.driver = self.selenium_manager.create_driver()
                
                # Пытаемся перейти на URL (внутри 3 попытки перезагрузки страницы)
                if not self.selenium_manager.navigate_to_url(self.category_url):
                    if driver_attempt < max_driver_retries - 1:
                        logger.warning(f"Не удалось загрузить страницу с драйвером #{driver_attempt + 1}, попытка с новым драйвером...")
                        continue
                    return False
                
                # Ожидаем контейнер товаров
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.ID, "contentScrollPaginator"))
                )
                
                logger.info(f"✓ Страница успешно загружена с драйвером #{driver_attempt + 1}")
                return True
                
            except TimeoutException:
                logger.error(f"Контейнер товаров не найден (драйвер #{driver_attempt + 1})")
                if driver_attempt < max_driver_retries - 1:
                    logger.info("Попытка с новым драйвером...")
                    continue
                return False
                
            except Exception as e:
                error_msg = str(e)
                
                # Если это ошибка блокировки после 3 попыток перезагрузки страницы
                if "Access blocked" in error_msg:
                    if driver_attempt < max_driver_retries - 1:
                        logger.warning(f"Драйвер #{driver_attempt + 1} заблокирован после 3 попыток перезагрузки, пробуем новый драйвер...")
                        continue  # Создадим новый драйвер на следующей итерации
                    else:
                        logger.error(f"Все {max_driver_retries} драйверов были заблокированы. Общее количество попыток: {max_driver_retries * 3}")
                        return False
                else:
                    logger.error(f"Ошибка загрузки страницы (драйвер #{driver_attempt + 1}): {e}")
                    if driver_attempt < max_driver_retries - 1:
                        logger.info("Попытка с новым драйвером...")
                        continue
                    return False
        
        logger.error(f"Не удалось загрузить страницу после {max_driver_retries} драйверов")
        return False
    
    def _collect_links(self):
        seen_urls = set()
        scroll_num = 0
        no_new_items_count = 0

        while len(self.collected_links) < self.max_products:
            scroll_num += 1
            current_items = self._extract_all_links()

            new_count = 0
            for url, img_url in current_items.items():
                if url not in seen_urls and len(self.collected_links) < self.max_products:
                    seen_urls.add(url)
                    self.collected_links[url] = img_url
                    new_count += 1

            logger.info(f"Скролл {scroll_num}: +{new_count}, всего {len(self.collected_links)}/{self.max_products}")

            if new_count == 0:
                no_new_items_count += 1
                if no_new_items_count >= 3:
                    break
            else:
                no_new_items_count = 0

            if len(self.collected_links) >= self.max_products:
                break

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(8)    
    
    def _extract_all_links(self) -> Dict[str, str]:
        try:
            container = self.driver.find_element(By.ID, "contentScrollPaginator")
            elements = container.find_elements(By.CSS_SELECTOR, "[class*='tile-root']")
            
            items = {}
            for element in elements:
                try:
                    link_element = element.find_element(By.CSS_SELECTOR, "a[data-prerender='true']")
                    href = link_element.get_attribute("href")
                    
                    img_element = element.find_element(By.CSS_SELECTOR, "img")
                    img_url = img_element.get_attribute("src")
                    
                    if href and href.startswith("https://www.ozon.ru/product/") and img_url:
                        items[href] = img_url
                except Exception:
                    continue
                
            return items
        except Exception as e:
            logger.warning(f"Ошибка извлечения ссылок: {e}")
            return {}
    
    def _create_output_folder(self):
        from pathlib import Path
        base_output_dir = Path(__file__).parent.parent.parent / "output"
        self.output_dir = base_output_dir / self.output_folder
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _save_links(self) -> bool:
        try:
            filename = f"links_{self.output_folder}.json"
            file_path = self.output_dir / filename
            
            links_to_save = dict(list(self.collected_links.items())[:self.max_products])
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(links_to_save, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения ссылок: {e}")
            return False
    
    def _cleanup(self):
        if self.selenium_manager:
            self.selenium_manager.close()
    
    def get_article_from_url(self, url: str) -> str:
        try:
            match = re.search(r'/product/[^/]+-(\d+)/', url)
            return match.group(1) if match else ""
        except Exception:
            return ""