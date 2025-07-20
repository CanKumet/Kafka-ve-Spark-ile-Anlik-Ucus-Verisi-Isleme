# producer/kafka_producer.py

import requests
from kafka import KafkaProducer
import json
import time

# Kafka üretici tanımı
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# API URL
url = "https://opensky-network.org/api/states/all"

# Alan isimleri
alanlar = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "heading", "vertical_rate", "sensors", "geo_altitude", "squawk",
    "spi", "position_source"
]

def veri_gonder():
    try:
        response = requests.get(url)
        response.raise_for_status()
        veri = response.json()

        if "states" in veri:
            for satir in veri["states"][:10]:  # İlk 10 kaydı gönder
                data = {alanlar[i]: satir[i] for i in range(len(alanlar))}
                producer.send("flight-data", value=data)
                print("Gönderilen veri:", data)

            producer.flush()
            print("Veriler Kafka'ya başarıyla gönderildi.")
        else:
            print("API'den 'states' verisi alınamadı.")
    except Exception as e:
        print("Hata oluştu:", str(e))

if __name__ == "__main__":
    while True:
        veri_gonder()
        time.sleep(20)  # 10 saniyede bir veriyi yenile ve gönder
