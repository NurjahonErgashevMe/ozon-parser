"""
Менеджер ресурсов для динамического распределения воркеров между пользователями
"""
import logging
import threading
import time
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class UserSession:
    user_id: str
    start_time: datetime
    current_stage: str  # 'links', 'products', 'sellers', 'idle'
    allocated_workers: int
    total_items: int
    processed_items: int = 0
    
class ResourceManager:
    """Менеджер для динамического распределения воркеров между пользователями"""
    
    # Константы
    MAX_TOTAL_WORKERS = 15
    MAX_WORKERS_PER_USER = 5
    MIN_WORKERS_PER_USER = 2
    SESSION_TIMEOUT_MINUTES = 30
    
    def __init__(self):
        self._lock = threading.RLock()
        self._active_sessions: Dict[str, UserSession] = {}
        self._cleanup_thread = None
        self._start_cleanup_thread()
        logger.info(f"ResourceManager инициализирован: макс {self.MAX_TOTAL_WORKERS} воркеров, макс {self.MAX_WORKERS_PER_USER} на пользователя")
    
    def _start_cleanup_thread(self):
        """Запускает поток для очистки устаревших сессий"""
        def cleanup_loop():
            while True:
                try:
                    self._cleanup_expired_sessions()
                    time.sleep(60)  # Проверяем каждую минуту
                except Exception as e:
                    logger.error(f"Ошибка в потоке очистки сессий: {e}")
                    time.sleep(60)
        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def start_parsing_session(self, user_id: str, stage: str, total_items: int) -> int:
        """
        Начинает новую сессию парсинга для пользователя
        
        Args:
            user_id: ID пользователя
            stage: Этап парсинга ('links', 'products', 'sellers')
            total_items: Общее количество элементов для обработки
            
        Returns:
            Количество выделенных воркеров
        """
        with self._lock:
            current_time = datetime.now()
            
            # Если у пользователя уже есть активная сессия, обновляем её
            if user_id in self._active_sessions:
                session = self._active_sessions[user_id]
                session.current_stage = stage
                session.total_items = total_items
                session.processed_items = 0
                # НЕ обновляем start_time, чтобы сохранить порядок пользователей
                logger.info(f"Обновлена сессия пользователя {user_id}: этап {stage}, {total_items} элементов")
            else:
                # Создаем новую сессию
                session = UserSession(
                    user_id=user_id,
                    start_time=current_time,
                    current_stage=stage,
                    allocated_workers=0,  # Будет установлено при перераспределении
                    total_items=total_items
                )
                self._active_sessions[user_id] = session
                logger.info(f"Создана новая сессия пользователя {user_id}: этап {stage}, {total_items} элементов")
            
            # ВСЕГДА перераспределяем воркеры в начале каждого этапа
            # Это гарантирует справедливое распределение на основе текущего количества активных пользователей
            self._redistribute_workers()
            
            allocated_workers = self._active_sessions[user_id].allocated_workers
            logger.info(f"Пользователь {user_id} получил {allocated_workers} воркеров для этапа {stage} (активных пользователей: {len(self._active_sessions)})")
            
            return allocated_workers
    
    def update_progress(self, user_id: str, processed_items: int):
        """Обновляет прогресс пользователя"""
        with self._lock:
            if user_id in self._active_sessions:
                self._active_sessions[user_id].processed_items = processed_items
    
    def finish_parsing_session(self, user_id: str):
        """Завершает сессию парсинга пользователя"""
        with self._lock:
            if user_id in self._active_sessions:
                del self._active_sessions[user_id]
                logger.info(f"Завершена сессия пользователя {user_id}")
                # Перераспределяем воркеры между оставшимися пользователями
                self._redistribute_workers()
    
    def get_active_users_count(self) -> int:
        """Возвращает количество активных пользователей"""
        with self._lock:
            return len(self._active_sessions)
    
    def get_user_workers(self, user_id: str) -> int:
        """Возвращает количество воркеров для пользователя"""
        with self._lock:
            if user_id in self._active_sessions:
                return self._active_sessions[user_id].allocated_workers
            return self.MIN_WORKERS_PER_USER
    
    def get_status(self) -> Dict:
        """Возвращает статус всех активных сессий"""
        with self._lock:
            status = {
                'total_active_users': len(self._active_sessions),
                'total_allocated_workers': sum(session.allocated_workers for session in self._active_sessions.values()),
                'sessions': {}
            }
            
            for user_id, session in self._active_sessions.items():
                progress_percent = 0
                if session.total_items > 0:
                    progress_percent = (session.processed_items / session.total_items) * 100
                
                status['sessions'][user_id] = {
                    'stage': session.current_stage,
                    'workers': session.allocated_workers,
                    'progress': f"{session.processed_items}/{session.total_items} ({progress_percent:.1f}%)",
                    'duration': str(datetime.now() - session.start_time).split('.')[0]
                }
            
            return status
    
    def _calculate_workers_for_new_user(self, total_items: int) -> int:
        """Рассчитывает количество воркеров для нового пользователя"""
        active_users = len(self._active_sessions)
        
        if active_users == 0:
            # Первый пользователь получает максимум воркеров
            return min(self.MAX_WORKERS_PER_USER, self._calculate_optimal_workers(total_items))
        
        # Рассчитываем справедливое распределение
        available_workers = self.MAX_TOTAL_WORKERS
        target_users = active_users + 1  # Включаем нового пользователя
        
        workers_per_user = max(self.MIN_WORKERS_PER_USER, 
                              min(self.MAX_WORKERS_PER_USER, 
                                  available_workers // target_users))
        
        return workers_per_user
    
    def _redistribute_workers(self):
        """Перераспределяет воркеры между всеми активными пользователями"""
        if not self._active_sessions:
            return
        
        active_users = len(self._active_sessions)
        available_workers = self.MAX_TOTAL_WORKERS
        
        # Справедливое распределение без приоритета по времени
        base_workers_per_user = max(self.MIN_WORKERS_PER_USER, 
                                   min(self.MAX_WORKERS_PER_USER, 
                                       available_workers // active_users))
        
        # Распределяем базовое количество всем пользователям
        total_allocated = 0
        for session in self._active_sessions.values():
            session.allocated_workers = base_workers_per_user
            total_allocated += base_workers_per_user
        
        # Распределяем оставшиеся воркеры равномерно (round-robin)
        remaining_workers = available_workers - total_allocated
        if remaining_workers > 0:
            # Создаем список пользователей для равномерного распределения
            user_list = list(self._active_sessions.values())
            user_index = 0
            
            while remaining_workers > 0:
                session = user_list[user_index]
                if session.allocated_workers < self.MAX_WORKERS_PER_USER:
                    session.allocated_workers += 1
                    remaining_workers -= 1
                
                user_index = (user_index + 1) % len(user_list)
                
                # Защита от бесконечного цикла
                if all(s.allocated_workers >= self.MAX_WORKERS_PER_USER for s in user_list):
                    break
        
        # Логируем новое распределение
        logger.info(f"Справедливое распределение воркеров для {active_users} пользователей:")
        for user_id, session in self._active_sessions.items():
            logger.info(f"  Пользователь {user_id}: {session.allocated_workers} воркеров ({session.current_stage})")
    
    def _calculate_optimal_workers(self, total_items: int) -> int:
        """Рассчитывает оптимальное количество воркеров для количества элементов"""
        if total_items <= 10:
            return 1
        elif total_items <= 25:
            return 2
        elif total_items <= 50:
            return 3
        elif total_items <= 100:
            return 4
        else:
            return 5  # Максимум 5 воркеров на пользователя
    
    def _cleanup_expired_sessions(self):
        """Очищает устаревшие сессии"""
        with self._lock:
            current_time = datetime.now()
            expired_users = []
            
            for user_id, session in self._active_sessions.items():
                if current_time - session.start_time > timedelta(minutes=self.SESSION_TIMEOUT_MINUTES):
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                logger.info(f"Удаление устаревшей сессии пользователя {user_id}")
                del self._active_sessions[user_id]
            
            if expired_users:
                self._redistribute_workers()

# Глобальный экземпляр менеджера ресурсов
resource_manager = ResourceManager()