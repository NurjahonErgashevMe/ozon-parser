import logging
from .config_loader import read_config, write_config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        pass
    
    def get_user_settings(self, user_id: str):
        config = read_config()
        
        # Получаем настройки для конкретного пользователя
        selected_fields_key = f"USER_{user_id}_SELECTED_FIELDS"
        field_order_key = f"USER_{user_id}_FIELD_ORDER"
        default_count_key = f"USER_{user_id}_DEFAULT_COUNT"
        
        if selected_fields_key in config and field_order_key in config:
            return {
                'selected_fields': config[selected_fields_key].split(',') if config[selected_fields_key] else [],
                'field_order': config[field_order_key].split(',') if config[field_order_key] else [],
                'default_product_count': int(config.get(default_count_key, 500))
            }
        else:
            # Настройки по умолчанию
            default_fields = ['name', 'company_name', 'product_url', 'image_url', 'description']
            self.save_user_settings(user_id, default_fields, default_fields, 500)
            return {
                'selected_fields': default_fields,
                'field_order': default_fields,
                'default_product_count': 500
            }
    
    def save_user_settings(self, user_id: str, selected_fields: list, field_order: list, default_count: int = 500):
        config = {
            f"USER_{user_id}_SELECTED_FIELDS": ','.join(selected_fields),
            f"USER_{user_id}_FIELD_ORDER": ','.join(field_order),
            f"USER_{user_id}_DEFAULT_COUNT": str(default_count)
        }
        
        return write_config(config)