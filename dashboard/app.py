from flask import Flask, render_template, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

# MongoDB bağlantısı
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["flightDB"]
collection = db["flight_data"]

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/veri')
def get_all_dashboard_data():
    try:
        # 1. Temel istatistikler
        total_flights = collection.count_documents({})
        five_minutes_ago = int((datetime.now() - timedelta(minutes=5)).timestamp())
        active_flights = collection.count_documents({"last_contact": {"$gte": five_minutes_ago}})
        airborne_flights = collection.count_documents({"on_ground": False})
        grounded_flights = collection.count_documents({"on_ground": True})

        stats = {
            'total_flights': total_flights,
            'active_flights': active_flights,
            'airborne_flights': airborne_flights,
            'grounded_flights': grounded_flights
        }

        # 2. Ülke bazlı uçuş sayıları
        pipeline_country = [
            {"$match": {"origin_country": {"$ne": None}}},
            {"$group": {"_id": "$origin_country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        result_countries = list(collection.aggregate(pipeline_country))
        countries = [{"country": item["_id"], "count": item["count"]} for item in result_countries]

        # 3. Son uçuşlar
        recent = list(collection.find(
            {"last_contact": {"$ne": None}},
            {
                "icao24": 1,
                "callsign": 1,
                "origin_country": 1,
                "baro_altitude": 1,
                "velocity": 1,
                "on_ground": 1,
                "last_contact": 1,
                "_id": 0
            }
        ).sort("last_contact", -1).limit(10))
        for flight in recent:
            if flight.get('last_contact'):
                flight['last_contact_readable'] = datetime.fromtimestamp(
                    flight['last_contact']
                ).strftime('%H:%M:%S')

        # 4. Hız dağılımı
        pipeline_velocity = [
            {"$match": {
                "velocity": {"$ne": None, "$gte": 0},
                "on_ground": False
            }},
            {"$project": {
                "speed_range": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lt": ["$velocity", 100]}, "then": "0-100 m/s"},
                            {"case": {"$lt": ["$velocity", 200]}, "then": "100-200 m/s"},
                            {"case": {"$lt": ["$velocity", 300]}, "then": "200-300 m/s"},
                            {"case": {"$lt": ["$velocity", 400]}, "then": "300-400 m/s"}
                        ],
                        "default": "400+ m/s"
                    }
                }
            }},
            {"$group": {"_id": "$speed_range", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        result_velocity = list(collection.aggregate(pipeline_velocity))
        velocity_data = [{"range": item["_id"], "count": item["count"]} for item in result_velocity]

        # 5. Yükseklik dağılımı (opsiyonel)
        pipeline_altitude = [
            {"$match": {
                "baro_altitude": {"$ne": None, "$gte": 0},
                "on_ground": False
            }},
            {"$project": {
                "altitude_range": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lt": ["$baro_altitude", 3000]}, "then": "0-3k ft"},
                            {"case": {"$lt": ["$baro_altitude", 10000]}, "then": "3k-10k ft"},
                            {"case": {"$lt": ["$baro_altitude", 20000]}, "then": "10k-20k ft"},
                            {"case": {"$lt": ["$baro_altitude", 30000]}, "then": "20k-30k ft"},
                            {"case": {"$lt": ["$baro_altitude", 40000]}, "then": "30k-40k ft"}
                        ],
                        "default": "40k+ ft"
                    }
                }
            }},
            {"$group": {"_id": "$altitude_range", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        result_altitude = list(collection.aggregate(pipeline_altitude))
        altitude_data = [{"range": item["_id"], "count": item["count"]} for item in result_altitude]

        # JSON olarak hepsini dön
        return jsonify({
            "stats": stats,
            "countries": countries,
            "recentFlights": recent,
            "velocity": velocity_data,
            "altitude": altitude_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
