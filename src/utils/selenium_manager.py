
import logging
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium_stealth import stealth
from typing import Optional

logger = logging.getLogger(__name__)

class SeleniumManager:
    
    def __init__(self, headless=True):
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
    
    def create_driver(self) -> webdriver.Chrome:
        chrome_options = Options()
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            

            stealth(driver,
                   languages=["ru-RU", "ru"],
                   vendor="Google Inc.",
                   platform="Win32",
                   webgl_vendor="Intel Inc.",
                   renderer="Intel Iris OpenGL Engine",
                   fix_hairline=True)
            

            driver.implicitly_wait(10)
            driver.set_page_load_timeout(30)
            

            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver = driver
            self.wait = WebDriverWait(driver, 10)
            
            logger.info("Chrome драйвер создан успешно")
            return driver
            
        except WebDriverException as e:
            logger.error(f"Ошибка создания Chrome драйвера: {e}")
            raise
    
    def create_driver_with_logging(self) -> webdriver.Chrome:
        chrome_options = Options()
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option('perfLoggingPrefs', {'enableNetwork': True, 'enablePage': False})
        chrome_options.add_experimental_option('loggingPrefs', {'performance': 'ALL'})
        
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            stealth(driver,
                   languages=["ru-RU", "ru"],
                   vendor="Google Inc.",
                   platform="Win32",
                   webgl_vendor="Intel Inc.",
                   renderer="Intel Iris OpenGL Engine",
                   fix_hairline=True)
            
            driver.implicitly_wait(10)
            driver.set_page_load_timeout(30)
            
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver = driver
            self.wait = WebDriverWait(driver, 10)
            
            logger.info("Chrome драйвер с логированием создан успешно")
            return driver
            
        except WebDriverException as e:
            logger.error(f"Ошибка создания Chrome драйвера с логированием: {e}")
            raise
    
    def navigate_to_url(self, url: str) -> bool:
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False
        
        try:
            logger.debug(f"Переход по URL: {url}")
            self.driver.get(url)
            

            self._wait_for_antibot_bypass()
            
            return True
            
        except TimeoutException:
            logger.error(f"Таймаут при загрузке: {url}")
            return False
        except WebDriverException as e:
            logger.error(f"Ошибка WebDriver: {e}")
            return False
    
    def wait_for_json_response(self, timeout: int = 30) -> Optional[str]:
        if not self.driver:
            return None
            
        try:
            logger.debug("Ожидание JSON ответа...")
            start_time = time.time()
            

            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            

            while time.time() - start_time < timeout:
                try:
                    page_source = self.driver.page_source
                    json_content = self._extract_json_from_html(page_source)
                    
                    if json_content:
                        try:
                            data = json.loads(json_content)
                            if 'widgetStates' in data:
                                logger.debug("JSON ответ с widgetStates найден")
                                return json_content
                        except json.JSONDecodeError:
                            pass
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.debug(f"Ошибка проверки содержимого страницы: {e}")
                    time.sleep(0.5)
                    continue
            
            logger.warning(f"Таймаут ожидания JSON ответа после {timeout} секунд")
            return self._extract_json_from_html(self.driver.page_source)
            
        except Exception as e:
            logger.error(f"Ошибка ожидания JSON ответа: {e}")
            return None
    
    def _extract_json_from_html(self, html_content: str) -> Optional[str]:
        try:
            import re
            

            pre_pattern = r'<pre[^>]*>(.*?)</pre>'
            pre_match = re.search(pre_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            if pre_match:
                json_content = pre_match.group(1).strip()
                logger.debug("JSON найден в <pre> теге")
                return json_content
            

            first_brace = html_content.find('{')
            last_brace = html_content.rfind('}')
            
            if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                json_content = html_content[first_brace:last_brace + 1]
                logger.debug("JSON найден по поиску скобок")
                return json_content
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка извлечения JSON из HTML: {e}")
            return None
    
    def _wait_for_antibot_bypass(self, max_wait_time: int = 60):
        start_time = time.time()
        reload_attempts = 0
        max_reload_attempts = 3
        
        while time.time() - start_time < max_wait_time:
            try:
                if self._is_blocked():
                    if reload_attempts < max_reload_attempts:
                        logger.info(f"Обнаружена блокировка, перезагрузка страницы (попытка {reload_attempts + 1}/{max_reload_attempts})")
                        self.driver.refresh()
                        reload_attempts += 1
                        time.sleep(5)
                        continue
                    else:
                        logger.warning("Превышено количество попыток перезагрузки, возвращаем новый драйвер")
                        raise Exception("Access blocked after retries")
                else:
                    logger.info("Антибот защита пройдена")
                    return
            except Exception as e:
                if "Access blocked" in str(e):
                    raise
                time.sleep(2)
                continue
        
        logger.warning(f"Антибот защита не пройдена за {max_wait_time} секунд")
        raise Exception("Antibot timeout")
    
    def _is_blocked(self) -> bool:
        if not self.driver:
            return True
            
        try:
            blocked_indicators = [
                "cloudflare", "checking your browser", "enable javascript",
                "access denied", "blocked", "ddos-guard", "проверка браузера",
                "доступ ограничен", "access restricted"
            ]
            
            page_source = self.driver.page_source.lower()
            
            for indicator in blocked_indicators:
                if indicator in page_source:
                    return True
                    
            return False
            
        except Exception:
            return True
    
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("Драйвер закрыт успешно")
            except Exception as e:
                logger.error(f"Ошибка закрытия драйвера: {e}")
            finally:
                self.driver = None
                self.wait = None