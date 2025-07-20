import subprocess
import time
import signal
import sys
import os


def start_services():
    processes = []

    print("Flight Tracking System başlatılıyor...")
    print("-" * 40)

    try:
        # 1. Kafka Producer başlat
        print("1. Kafka Producer başlatılıyor...")
        producer = subprocess.Popen([sys.executable, "producer/kafka_producer.py"])
        processes.append(("Kafka Producer", producer))
        time.sleep(3)

        # 2. Spark Consumer başlat
        print("2. Spark Consumer başlatılıyor...")
        consumer = subprocess.Popen([sys.executable, "consumer/spark_consumer.py"])
        processes.append(("Spark Consumer", consumer))
        time.sleep(15)

        # 3. Flask App başlat
        print("3. Flask Web App başlatılıyor...")
        webapp = subprocess.Popen([sys.executable, "dashboard/app.py"])
        processes.append(("Flask App", webapp))

        print("-" * 40)
        print("✅ Tüm servisler başlatıldı!")
        print("🌐 Web arayüz: http://localhost:5000")
        print("⏹️  Durdurmak için Ctrl+C tuşlayın")
        print("-" * 40)

        # Servislerin çalışmasını bekle
        while True:
            time.sleep(1)

            # Herhangi bir servis durmuş mu kontrol et
            for name, process in processes:
                if process.poll() is not None:
                    print(f"❌ {name} durdu!")

    except KeyboardInterrupt:
        print("\n🛑 Sistem kapatılıyor...")

        # Tüm servisleri kapat
        for name, process in processes:
            print(f"⏹️  {name} kapatılıyor...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        print("✅ Tüm servisler kapatıldı")


if __name__ == "__main__":
    # Gerekli dosyaların varlığını kontrol et
    required_files = ["producer/kafka_producer.py", "consumer/spark_consumer.py", "dashboard/app.py"]

    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        print(f"❌ Eksik dosyalar: {missing}")
        sys.exit(1)

    start_services()