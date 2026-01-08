# Ozon Parser

Парсер товаров Ozon.ru с GUI и Telegram-ботом. Многопоточный сбор данных о товарах и продавцах.

## Demo

<video src="assets/demo.mp4" controls width="100%"></video>


## Возможности

- ✅ Парсинг до 10,000 товаров из категорий
- ✅ Данные о продавцах: ИНН, рейтинг, статистика
- ✅ Многопоточность (до 5 воркеров)
- ✅ Экспорт в Excel + JSON
- ✅ Telegram бот для управления
- ✅ GUI интерфейс

## Установка

```bash
git clone https://github.com/NurjahonErgashevMe/ozon-parser
cd ozon-parser
pip install -r requirements.txt
```

**Требования**: Python 3.11, Chrome браузер

## Запуск

```bash
python main.py          # GUI
python bot.py           # Только Telegram бот
python app.py           # CLI
```

## Конфигурация

Создайте `config.txt`:

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_user_id
USER_your_user_id_SELECTED_FIELDS=name,company_name,inn,price
USER_your_user_id_FIELD_ORDER=name,company_name,inn,price
USER_your_user_id_DEFAULT_COUNT=500
```

## Доступные поля

| Поле | Описание |
|------|----------|
| `article` | Артикул товара |
| `name` | Название товара |
| `seller_name` | Имя продавца |
| `company_name` | Название компании |
| `inn` | ИНН продавца |
| `card_price` | Цена по карте |
| `price` | Текущая цена |
| `original_price` | Старая цена |
| `product_url` | Ссылка на товар |
| `image_url` | Ссылка на изображение |
| `orders_count` | Количество заказов |
| `reviews_count` | Количество отзывов |
| `average_rating` | Средний рейтинг |
| `working_time` | Дата регистрации |

## Особенности

- **Обход блокировки**: 3 драйвера × 3 попытки = 9 попыток обхода антибота
- **Резервный поиск seller_id**: если не найден в основных данных, ищет по всему JSON
- **Умное управление ресурсами**: автоматическое распределение воркеров между пользователями
- **Headless режим**: настраивается в `src/config/settings.py`

## Структура вывода

```
output/
└── category_name_DD.MM.YYYY_HH-MM-SS/
    ├── links_*.json               # Собранные ссылки
    ├── category_*.json            # Данные в JSON
    └── category_*.xlsx            # Excel отчет
```

## Troubleshooting

**Парсинг селлеров не работает?**
- Проверьте что в `SELECTED_FIELDS` есть хотя бы одно поле селлера: `inn`, `company_name`, `seller_name`, `orders_count`, `reviews_count`, `average_rating`, `working_time`

**Блокировка Ozon?**
- Установите `HEADLESS = False` в `src/config/settings.py`
- Используйте прокси
- Увеличьте задержки между запросами

## Лицензия

MIT License