import requests
import pandas as pd
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env.local")
WAQI_TOKEN = os.getenv("WAQI_TOKEN")

if not WAQI_TOKEN:
    print("❌ WAQI API token not found. Add it to .env.local as WAQI_TOKEN.")
    exit()

# Configuration
openmeteo_url = "https://api.open-meteo.com/v1/forecast"
hourly_params = "temperature_2m,relative_humidity_2m,windspeed_10m"
output_path = "data/raw/waqi_india_pm25_weather.csv"
os.makedirs("data/raw", exist_ok=True)

# List of major Indian cities
indian_cities = [
    "Delhi", "Mumbai", "Kolkata", "Chennai", "Bangalore", "Hyderabad", "Ahmedabad",
    "Pune", "Lucknow", "Jaipur", "Patna", "Bhopal", "Chandigarh", "Nagpur", "Indore"
]

def get_pm25_data(city):
    url = f"https://api.waqi.info/feed/{city}/?token={WAQI_TOKEN}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if data["status"] != "ok":
            return None

        d = data["data"]
        iaqi = d.get("iaqi", {})
        return {
            "city": city,
            "timestamp": d["time"]["s"],
            "lat": d["city"]["geo"][0],
            "lon": d["city"]["geo"][1],
            "PM2.5": iaqi.get("pm25", {}).get("v", None)
        }
    except:
        return None

def get_weather(lat, lon, timestamp):
    url = f"{openmeteo_url}?latitude={lat}&longitude={lon}&hourly={hourly_params}&timezone=auto"
    try:
        res = requests.get(url, timeout=10)
        data = res.json().get("hourly", {})
        if not data:
            return None
        df = pd.DataFrame({
            "timestamp": pd.to_datetime(data["time"]),
            "temperature": data["temperature_2m"],
            "humidity": data["relative_humidity_2m"],
            "wind_speed": data["windspeed_10m"]
        })
        pm_time = pd.to_datetime(timestamp)
        df["diff"] = (df["timestamp"] - pm_time).abs()
        closest = df.sort_values("diff").iloc[0]
        return {
            "temperature": closest["temperature"],
            "humidity": closest["humidity"],
            "wind_speed": closest["wind_speed"]
        }
    except:
        return None

def fetch_india_data():
    all_data = []
    print("🚀 Fetching PM2.5 & Weather data for major Indian cities...")

    for i, city in enumerate(indian_cities):
        print(f"➡️ {i+1}/{len(indian_cities)}: {city}")
        pm_data = get_pm25_data(city)
        if not pm_data:
            print(f"❌ Skipping {city} (no air data)")
            continue

        weather = get_weather(pm_data["lat"], pm_data["lon"], pm_data["timestamp"])
        if weather:
            pm_data.update(weather)
        else:
            print(f"⚠️ No weather data for {city}")
            pm_data.update({"temperature": None, "humidity": None, "wind_speed": None})

        all_data.append(pm_data)
        time.sleep(1)

    df = pd.DataFrame(all_data)
    df.to_csv(output_path, index=False)
    print(f"\n✅ Final dataset saved to: {output_path}")

if __name__ == "__main__":
    fetch_india_data()
