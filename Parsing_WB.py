import asyncio
import logging
import time
import json
import pandas as pd
from aiogram import Bot
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from dotenv import load_dotenv
import os

# Загрузка переменных из файла .env (необходимо указать ваш токен и ID чата куда вы хотите получать сообщения от бота)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

logging.basicConfig(filename='notification.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Загрузка reviews из файла JSON, если он существует
if os.path.exists('reviews.json'):
    with open('reviews.json', 'r') as file:
        processed_reviews = json.load(file)
else:
    processed_reviews = {}


# Функция для отправки уведомления в Telegram
async def notification(bot, chat_id, message):
    try:
        await bot.send_message(chat_id=chat_id, text=message)
        logging.info(f"Уведомление успешно отправлено: {message}")
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления: {e}")


# Функция для получения первого отзыва о товаре
async def first_feedback(driver):
    try:
        page_content = driver.page_source
        soup = BeautifulSoup(page_content, 'html.parser')

        rating_tag = soup.find('b', class_='rating-product__numb')
        current_rating = rating_tag.text.strip() if rating_tag else None

        feedback_item = soup.find('li', class_='comments__item feedback j-feedback-slide')
        if feedback_item:
            author_tag = feedback_item.find('p', class_='feedback__header')
            author = author_tag.text.strip() if author_tag else None

            date_tag = feedback_item.find('span', class_='feedback__date')
            date = date_tag['content'] if date_tag else None

            text_tag = feedback_item.find('p', class_='feedback__text')
            text = text_tag.text.strip() if text_tag else None

            rating_stars = feedback_item.find_all('span',
                                                  class_=lambda value: value and 'star' in value and value[
                                                      -1] in '1234')
            rating = max(int(star.get('class')[-1][-1]) for star in rating_stars) if rating_stars else 5

            text = text.replace('ещё', '')

            feedback_data = {'author': author, 'date': date, 'text': text, 'rating': rating}
        else:
            feedback_data = None

        return feedback_data, current_rating

    except Exception as e:
        logging.error(f"Ошибка при получении первого отзыва: {e}")
        return None, None


# Функция для обработки отзывов о товаре
async def process_feedback(bot, chat_id, feedback, sku):
    try:
        for review in feedback:
            if 1 <= review['rating'] <= 4:
                if review['text'] not in processed_reviews.get(sku, []):
                    message = f"Негативный отзыв/{sku}/{review['rating']} звезд/{review['text']}"
                    await notification(bot, chat_id, message)
                    logging.info(f"Новый негативный отзыв о товаре {sku} обработан")
                    # Добавляем отзыв в processed_reviews
                    processed_reviews.setdefault(sku, []).append(review['text'])
    except Exception as e:
        logging.error(f"Ошибка при обработке отзыва для товара {sku}: {e}")


# Функция для открытия браузера и получения отзывов о товаре
async def get_reviews(bot, chat_id, url, sku):
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(1)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.5);")
        time.sleep(1)

        see_all_reviews_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn-base.comments__btn-all")))
        see_all_reviews_button.click()
        time.sleep(3)

        feedback_data, current_rating = await first_feedback(driver)
        if feedback_data:
            message = f"Негативный отзыв/{sku}/{feedback_data['rating']} звезд/{feedback_data['text']}"
            message += f"\nТекущий рейтинг товара: {current_rating}"
            await notification(bot, chat_id, message)
            logging.info(f"Негативный отзыв о товаре {sku} найден")
        else:
            print("Отзывы отсутствуют")

    except Exception as e:
        logging.error(f"Ошибка при обработке URL {url}: {e}")

    finally:
        if driver:
            driver.quit()


# Основная функция
async def main():
    try:
        df = pd.read_excel('test.xlsx', header=None)
        base_url = "https://www.wildberries.ru/catalog/"
        sku_list = df[0].astype(str).tolist()

        bot = Bot(token=BOT_TOKEN)

        while True:
            for sku in sku_list:
                product_url = f"{base_url}{sku}/detail.aspx"
                await get_reviews(bot, CHAT_ID, product_url, sku)
                time.sleep(2)

            # После обработки всех отзывов сохраняем reviews в файле JSON
            with open('reviews.json', 'w') as files:
                json.dump(processed_reviews, files)

            # пауза перед повторной проверкой новых отзывов
            await asyncio.sleep(300)

    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
