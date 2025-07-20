from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StringType, DoubleType, LongType, BooleanType
from pymongo import MongoClient
import os
import json

os.environ["PYSPARK_PYTHON"] = "python"
os.environ["PYSPARK_DRIVER_PYTHON"] = "python"

# MongoDB bağlantısı
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["flightDB"]
collection = db["flight_data"]

# Mongo'ya kayıt fonksiyonu
def save_to_mongodb(df, epoch_id):
    data = df.toJSON().map(lambda x: json.loads(x)).collect()
    print(f"[*] Gelen veri: {data}")  # Bunu ekle
    if data:
        collection.insert_many(data)
        print(f"[✓] {len(data)} kayıt MongoDB'ye eklendi.")
    else:
        print("[!] Hiç veri alınamadı.")


# Spark oturumu başlat
spark = SparkSession.builder \
    .appName("KafkaFlightConsumerTest") \
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# JSON verisinin şeması
schema = StructType() \
    .add("icao24", StringType()) \
    .add("callsign", StringType()) \
    .add("origin_country", StringType()) \
    .add("time_position", LongType()) \
    .add("last_contact", LongType()) \
    .add("longitude", DoubleType()) \
    .add("latitude", DoubleType()) \
    .add("baro_altitude", DoubleType()) \
    .add("on_ground", BooleanType()) \
    .add("velocity", DoubleType()) \
    .add("heading", DoubleType()) \
    .add("vertical_rate", DoubleType()) \
    .add("geo_altitude", DoubleType()) \
    .add("squawk", StringType()) \
    .add("spi", BooleanType()) \
    .add("position_source", LongType())

# Kafka'dan veri oku
df_kafka = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "host.docker.internal:9092") \
    .option("subscribe", "flight-data") \
    .option("startingOffsets", "latest") \
    .load()

# JSON olarak parse et
df_parsed = df_kafka.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), schema).alias("data")) \
    .select("data.*")

# Veriyi hem console'a yaz hem de MongoDB'ye kaydet
df_parsed.writeStream \
    .foreachBatch(save_to_mongodb) \
    .outputMode("append") \
    .start()

# Ayrıca terminalde de göster (kontrol amaçlı)
df_parsed.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", False) \
    .start() \
    .awaitTermination()
