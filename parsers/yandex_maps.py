import datetime
import itertools
import json
import sys

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import urllib.parse

def loading_animation(text, duration=3):
    spinner = itertools.cycle(['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏'])
    end_time = time.time() + duration
    while time.time() < end_time:
        sys.stdout.write(f'\r{next(spinner)} {text}')
        sys.stdout.flush()
        time.sleep(0.1)
    print('\r✅ Завершено'.ljust(50))

def scroll_until_all_working(driver, max_closed_in_row=5, max_idle_scrolls=3):
    def log_inline(text, icon="🔍"):
        print(f"\r{icon} {text}...", end='')
        sys.stdout.flush()

    def log_final(text, icon="✅"):
        print(f"\r{icon} {text}".ljust(50))

    try:
        scroll_container = driver.execute_script(
            "return document.querySelector('div.scroll__container')?.parentElement"
        )

        if not scroll_container:
            log_final("Контейнер скролла не найден", "❌")
            return

        log_inline("Ищем пункты выдачи", "🔍")
        closed_in_row = 0
        same_count_scrolls = 0
        prev_count = 0

        while True:
            # Получаем все item'ы
            items = driver.find_elements(By.CSS_SELECTOR, 'li.search-snippet-view')

            # Проверка на "больше не работает"
            new_closed = 0
            for el in items[-10:]:  # проверяем только последние 10 (оптимизация)
                try:
                    status = el.find_element(By.CLASS_NAME, 'business-working-status-view').text
                    if status.strip() == 'Больше не работает':
                        new_closed += 1
                except Exception:
                    continue

            if new_closed >= max_closed_in_row:
                log_final(f"Обнаружено {new_closed} закрытых ПВЗ подряд. Останавливаемся", "⛔")
                break

            # Проверка на завершение (список не растёт)
            current_count = len(items)
            if current_count == prev_count:
                same_count_scrolls += 1
                log_inline(f"Новых элементов нет ({current_count}) [{same_count_scrolls}/{max_idle_scrolls}]", "⚠️")
                if same_count_scrolls >= max_idle_scrolls:
                    log_final("Список закончился", "✅")
                    break
            else:
                same_count_scrolls = 0
                prev_count = current_count
                log_inline(f"📦 Найдено элементов: {current_count}")

            # Скроллим вниз
            driver.execute_script(
                "document.querySelector('div.scroll__container').scrollTop += 1000;"
            )
            time.sleep(1.2)

    except Exception as e:
        log_final(f"Ошибка при скроллинге: {e}", "❌")


def get_places(query: str, city: str):
    def log_inline(text, icon="🌍"):
        print(f"\r{icon} {text}", end='')
        sys.stdout.flush()

    def log_final(text, icon="✅"):
        print(f"\r{icon} {text}".ljust(50))

    global places
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)...")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=options)
    driver.get("https://yandex.ru/maps/")


    try:
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[contains(@class,"input__control")]'))
        )
        search_input.send_keys(query)
        search_input.submit()


        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'li.search-snippet-view'))
        )

        # Скролл
        # try:
        #     scroll_container = driver.execute_script(
        #         "return document.querySelector('div.scroll__container')?.parentElement"
        #     )
        #
        #     if scroll_container:
        #         last_count = -1
        #         for _ in range(1):
        #             driver.execute_script(
        #                 "document.querySelector('div.scroll__container').scrollTop += 1500;"
        #             )
        #             time.sleep(1)
        #             items = driver.find_elements(By.CSS_SELECTOR, 'li.search-snippet-view')
        #             if len(items) == last_count:
        #                 break
        #             last_count = len(items)
        # except Exception as e:
        #     print("⚠ Пропущен скроллинг: список не найден или произошла ошибка.")

        scroll_until_all_working(driver)

        # Сбор
        places = []
        for el in driver.find_elements(By.CSS_SELECTOR, 'li.search-snippet-view'):
            try:
                name = el.find_element(By.CLASS_NAME, 'search-business-snippet-view__title').text
                address = el.find_element(By.CLASS_NAME, 'search-business-snippet-view__address').text
                working_status = el.find_element(By.CLASS_NAME, 'business-working-status-view').text
                if working_status == 'Больше не работает':
                    continue


                places.append({
                    "id": len(places) + 1,
                    "name": name,
                    "address": address,
                })
            except Exception:
                continue

        try:
            for item in places:
                try:
                    address = f"{item['address']}, {city}"
                    log_inline(f"Ищем координаты для: {address}")

                    # Найди поле поиска заново (если элемент перерисовывается — старый уже не работает)
                    search_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input.input__control"))
                    )

                    # Очисти через Ctrl+A + Backspace
                    search_input.send_keys(Keys.CONTROL + 'a')
                    search_input.send_keys(Keys.BACKSPACE)

                    # Отправь новый запрос
                    search_input.send_keys(address)
                    search_input.send_keys(Keys.ENTER)
                    time.sleep(1)

                    # Жди координаты
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.toponym-card-title-view__coords-badge'))
                    )

                    coords = driver.find_element(By.CSS_SELECTOR, 'div.toponym-card-title-view__coords-badge').text
                    item['coords'] = coords
                    log_final(f"Координаты: {coords}")


                except Exception as e:
                    log_final(f"Ошибка для {item['address']}: {e}", "❌")
        except Exception as e:
            print('coord error')
    finally:

        driver.quit()

        export = input('Хотели бы вы экспортировать в JSON?(y/n): ')

        if export.lower() == 'y':

            now = datetime.datetime.now()

            filename = f"./{now.date()}_{now.time().strftime('%H-%M-%S')}.json"


            with open(filename, "w", encoding="utf-8") as f:

                json.dump(places, f, ensure_ascii=False, indent=2)

            print(f'Файл успешно создан: {filename}')

        else:

            print()

    return places