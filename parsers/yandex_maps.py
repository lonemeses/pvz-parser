from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import urllib.parse

def get_places(query: str):
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
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
        try:
            scroll_container = driver.execute_script(
                "return document.querySelector('div.scroll__container')?.parentElement"
            )

            if scroll_container:
                last_count = -1
                for _ in range(100):
                    driver.execute_script(
                        "document.querySelector('div.scroll__container').scrollTop += 1500;"
                    )
                    time.sleep(1)
                    items = driver.find_elements(By.CSS_SELECTOR, 'li.search-snippet-view')
                    if len(items) == last_count:
                        break
                    last_count = len(items)
        except Exception as e:
            print("⚠ Пропущен скроллинг: список не найден или произошла ошибка.")

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

        return places

    finally:
        driver.quit()
