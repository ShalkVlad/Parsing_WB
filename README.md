# Проект мониторинга отзывов на товары в Wildberries

Этот проект представляет собой инструмент для мониторинга негативных отзывов на товары в интернет-магазине Wildberries и отправки уведомлений в группу Telegram.

## Особенности

- Поиск и анализ негативных отзывов на товары в Wildberries.
- Отправка уведомлений в группу Telegram с информацией о негативных отзывах.
- Проверка на наличие новых отзывов и исключение повторных уведомлений.

## Использование

1. Установите необходимые зависимости, запустив команду `pip install -r requirements.txt`.
2. Запустите основной скрипт, выполнив команду `python main.py`.
3. Проверьте группу Telegram для получения уведомлений о негативных отзывах.

Проект поддерживает работу с файлом Excel, в котором указываются SKU товаров Wildberries. SKU - это уникальный идентификатор товара в магазине Wildberries. Скрипт автоматически ищет негативные отзывы для каждого товара, указанного в файле Excel.