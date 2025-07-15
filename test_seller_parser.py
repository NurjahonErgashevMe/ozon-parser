import logging
import sys
from src.parsers.seller_parser import OzonSellerParser
from src.utils.json_utils import find_components_recursive

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def test_seller_parser():
    # Тестовые ID продавцов - добавлены проблемные ID
    seller_ids = ["70000", "167977", "1000", "1239302", "1639387"]
    
    # Создаем парсер
    parser = OzonSellerParser(max_workers=2)
    
    # Запускаем парсинг
    results = parser.parse_sellers(seller_ids)
    
    # Выводим результаты
    print(f"\nПолучено {len(results)} результатов:")
    
    success_count = 0
    for result in results:
        print(f"\nПродавец ID: {result.seller_id}")
        print(f"Успех: {result.success}")
        if result.success:
            success_count += 1
            print(f"Название компании: {result.company_name}")
            print(f"ИНН: {result.inn}")
            print(f"Количество заказов: {result.orders_count}")
            print(f"Количество отзывов: {result.reviews_count}")
            print(f"Работает с Ozon: {result.working_time}")
            print(f"Средняя оценка: {result.average_rating}")
        else:
            print(f"Ошибка: {result.error}")
    
    print(f"\nУспешно обработано: {success_count}/{len(results)} продавцов")

# Тест функции рекурсивного поиска компонентов
def test_find_components():
    # Пример вложенной структуры
    test_layout = [
        {
            "component": "row",
            "stateId": "row-1",
            "placeholders": [
                {
                    "name": "default",
                    "widgets": [
                        {
                            "component": "column",
                            "stateId": "column-1",
                            "placeholders": [
                                {
                                    "name": "default",
                                    "widgets": [
                                        {
                                            "component": "textBlock",
                                            "stateId": "textBlock-1"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "component": "cellList",
            "stateId": "cellList-1"
        }
    ]
    
    # Тестируем поиск textBlock
    text_blocks = find_components_recursive(test_layout, "textBlock")
    print(f"\nНайдено textBlock компонентов: {len(text_blocks)}")
    for block in text_blocks:
        print(f"stateId: {block.get('stateId')}")
    
    # Тестируем поиск cellList
    cell_lists = find_components_recursive(test_layout, "cellList")
    print(f"\nНайдено cellList компонентов: {len(cell_lists)}")
    for cell in cell_lists:
        print(f"stateId: {cell.get('stateId')}")

if __name__ == "__main__":
    # Тестируем функцию поиска компонентов
    test_find_components()
    
    # Тестируем парсер продавцов
    test_seller_parser()