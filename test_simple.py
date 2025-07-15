#!/usr/bin/env python3
"""
Простой тест основной логики парсера
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logging
from src.config.settings import Settings
from src.parsers.link_parser import OzonLinkParser
from src.parsers.product_parser import OzonProductParser
import logging

def test_link_parser():
    """Тест парсера ссылок"""
    print("=== ТЕСТ ПАРСЕРА ССЫЛОК ===")
    
    category_url = "https://ozon.ru/category/sistemnye-bloki-15704/"
    max_products = 10  # Для теста берем только 10 товаров
    
    parser = OzonLinkParser(category_url, max_products)
    success, links = parser.start_parsing()
    
    if success and links:
        print(f"✅ Успешно собрано {len(links)} ссылок")
        for i, (url, img_url) in enumerate(list(links.items())[:3], 1):
            print(f"{i}. {url}")
            print(f"   Изображение: {img_url}")
        return links
    else:
        print("❌ Ошибка сбора ссылок")
        return {}

def test_product_parser(links):
    """Тест парсера товаров"""
    print("\n=== ТЕСТ ПАРСЕРА ТОВАРОВ ===")
    
    if not links:
        print("❌ Нет ссылок для тестирования")
        return
    
    # Берем только первые 3 ссылки для теста
    test_links = dict(list(links.items())[:3])
    
    parser = OzonProductParser(max_workers=2)
    results = parser.parse_products(test_links)
    
    print(f"Обработано {len(results)} товаров:")
    
    for result in results:
        print(f"\n📦 Артикул: {result.article}")
        print(f"   Название: {result.name}")
        print(f"   Компания: {result.company_name}")
        print(f"   Цена с картой: {result.card_price}")
        print(f"   Обычная цена: {result.price}")
        print(f"   Оригинальная цена: {result.original_price}")
        print(f"   Успех: {'✅' if result.success else '❌'}")
        if result.error:
            print(f"   Ошибка: {result.error}")

def main():
    """Главная функция теста"""
    setup_logging(log_level="INFO")
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Запуск простого теста парсера")
        
        # Тест 1: Парсинг ссылок
        links = test_link_parser()
        
        # Тест 2: Парсинг товаров
        if links:
            test_product_parser(links)
        
        print("\n🎉 Тест завершен!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Тест прерван пользователем")
    except Exception as e:
        logger.error(f"Ошибка теста: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()