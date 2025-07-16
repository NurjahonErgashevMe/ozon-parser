import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: Path = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "bot_settings.db"
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id TEXT PRIMARY KEY,
                        selected_fields TEXT,
                        field_order TEXT,
                        default_product_count INTEGER DEFAULT 500
                    )
                ''')
                
                # Миграция: добавляем столбец если его нет
                try:
                    conn.execute('ALTER TABLE user_settings ADD COLUMN default_product_count INTEGER DEFAULT 500')
                except sqlite3.OperationalError:
                    pass  # Столбец уже существует
                
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
    
    def get_user_settings(self, user_id: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT selected_fields, field_order, default_product_count FROM user_settings WHERE user_id = ?',
                    (user_id,)
                )
                result = cursor.fetchone()
                if result:
                    return {
                        'selected_fields': result[0].split(',') if result[0] else [],
                        'field_order': result[1].split(',') if result[1] else [],
                        'default_product_count': result[2] if result[2] else 500
                    }
                else:
                    # Настройки по умолчанию
                    default_fields = ['name', 'company_name', 'product_url', 'image_url']
                    self.save_user_settings(user_id, default_fields, default_fields, 500)
                    return {
                        'selected_fields': default_fields,
                        'field_order': default_fields,
                        'default_product_count': 500
                    }
        except Exception as e:
            logger.error(f"Ошибка получения настроек: {e}")
            return {
                'selected_fields': ['name', 'company_name', 'product_url', 'image_url'],
                'field_order': ['name', 'company_name', 'product_url', 'image_url'],
                'default_product_count': 500
            }
    
    def save_user_settings(self, user_id: str, selected_fields: list, field_order: list, default_count: int = 500):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO user_settings (user_id, selected_fields, field_order, default_product_count)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, ','.join(selected_fields), ','.join(field_order), default_count))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
            return False