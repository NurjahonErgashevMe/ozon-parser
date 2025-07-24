#!/usr/bin/env python3
"""
Тест распределения ресурсов между пользователями
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.resource_manager import ResourceManager

def test_resource_distribution():
    """Тестирует распределение ресурсов между пользователями"""
    
    print("🧪 Тест распределения ресурсов")
    print("=" * 50)
    
    # Создаем новый менеджер ресурсов для теста
    rm = ResourceManager()
    
    print(f"📊 Настройки:")
    print(f"   Макс воркеров всего: {rm.MAX_TOTAL_WORKERS}")
    print(f"   Макс на пользователя: {rm.MAX_WORKERS_PER_USER}")
    print(f"   Мин на пользователя: {rm.MIN_WORKERS_PER_USER}")
    print()
    
    # Сценарий 1: Один пользователь
    print("📋 Сценарий 1: Один пользователь парсит 500 товаров")
    workers1 = rm.start_parsing_session("user1", "products", 500)
    print(f"   User1 получил: {workers1} воркеров")
    status = rm.get_status()
    print(f"   Всего используется: {status['total_allocated_workers']}/{rm.MAX_TOTAL_WORKERS}")
    print()
    
    # Сценарий 2: Второй пользователь присоединяется
    print("📋 Сценарий 2: Второй пользователь начинает парсинг 300 товаров")
    workers2 = rm.start_parsing_session("user2", "products", 300)
    print(f"   User2 получил: {workers2} воркеров")
    
    # Проверяем перераспределение для первого пользователя
    workers1_new = rm.get_user_workers("user1")
    print(f"   User1 теперь имеет: {workers1_new} воркеров (было {workers1})")
    
    status = rm.get_status()
    print(f"   Всего используется: {status['total_allocated_workers']}/{rm.MAX_TOTAL_WORKERS}")
    print()
    
    # Сценарий 3: Третий пользователь присоединяется
    print("📋 Сценарий 3: Третий пользователь начинает парсинг 100 товаров")
    workers3 = rm.start_parsing_session("user3", "sellers", 100)
    print(f"   User3 получил: {workers3} воркеров")
    
    # Проверяем перераспределение для всех
    workers1_final = rm.get_user_workers("user1")
    workers2_final = rm.get_user_workers("user2")
    
    print(f"   User1 теперь имеет: {workers1_final} воркеров")
    print(f"   User2 теперь имеет: {workers2_final} воркеров")
    print(f"   User3 имеет: {workers3} воркеров")
    
    status = rm.get_status()
    print(f"   Всего используется: {status['total_allocated_workers']}/{rm.MAX_TOTAL_WORKERS}")
    print()
    
    # Сценарий 4: Первый пользователь переходит к следующему этапу
    print("📋 Сценарий 4: User1 переходит к парсингу продавцов (50 продавцов)")
    workers1_sellers = rm.start_parsing_session("user1", "sellers", 50)
    print(f"   User1 получил для sellers: {workers1_sellers} воркеров")
    
    status = rm.get_status()
    print(f"   Всего используется: {status['total_allocated_workers']}/{rm.MAX_TOTAL_WORKERS}")
    print()
    
    # Показываем финальный статус
    print("📊 Финальный статус:")
    status = rm.get_status()
    for user_id, session_info in status['sessions'].items():
        print(f"   {user_id}: {session_info['workers']} воркеров, этап: {session_info['stage']}")
    
    print()
    print("✅ Тест завершен!")

if __name__ == "__main__":
    test_resource_distribution()