# producer/get_flights.py

import requests
import json
import time


def get_opensky_data():
    url = "https://opensky-network.org/api/states/all"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        print(f"🔄 API'den alınan uçuş sayısı: {len(data['states'])}")
        print("-" * 50)

        # İlk 5 uçuşu terminalde göster
        for flight in data["states"][:5]:
            flight_info = {
                "uçuş_kodu": flight[1].strip() if flight[1] else "YOK",
                "ülke": flight[2],
                "enlem": flight[6],
                "boylam": flight[5],
                "irtifa": flight[7],
                "hız": flight[9]
            }
            print(flight_info)
    except Exception as e:
        print("❌ Hata oluştu:", e)


# 10 saniyede bir veri çek
if __name__ == "__main__":
    while True:
        get_opensky_data()
        time.sleep(10)
