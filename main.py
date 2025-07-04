import argparse
from parsers import yandex_maps

def main():
    parser = argparse.ArgumentParser(description="Парсер пунктов выдачи заказов")
    parser.add_argument("--search", help="Бренд для поиска в Яндекс.Картах (ozon, wildberries)")
    parser.add_argument("--city", help="Город для фильтрации")

    args = parser.parse_args()


    if not args.search or not args.city:
        print("Для Яндекс.Карт необходимо указать --search и --city")
        return
    query = f"{args.search} {args.city}"
    data = yandex_maps.get_places(query)

    for entry in data:
        print(entry)

if __name__ == "__main__":
    main()