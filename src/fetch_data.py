import requests
import pandas as pd
import os
import datetime
import time

def fetch_cpcb_and_weather_data():
    """
    Fetches live PM2.5 measurements from OpenAQ API for India
    and corresponding meteorological data (forecast) from Open-Meteo API.
    """

    # --- OpenAQ Configuration (PM2.5 Ground Data) ---
    # OpenAQ is a free, open API that aggregates air quality data globally.
    # Docs: https://docs.openaq.org/
    openaq_url = "https://api.openaq.org/v2/measurements"
    openaq_params = {
        "country": "IN",
        "limit": 10000, # Max records to fetch. Adjust based on your needs and API limits.
        "parameter": "pm25",
        "sort": "desc",
        "order_by": "datetime",
        # Fetch data from the last 24 hours to get recent readings.
        "date_from": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat(),
        "has_geo": "true" # Ensure locations have latitude/longitude
    }
    # Optional: Include your email for OpenAQ's 'polite pool' for better reliability.
    # openaq_params["mailto"] = "your.email@example.com" 

    # --- Open-Meteo Configuration (Meteorological Data) ---
    # Open-Meteo provides free weather forecast and historical data APIs.
    # Docs: https://open-meteo.com/en/docs
    openmeteo_base_url = "https://api.open-meteo.com/v1/forecast"
    # We fetch hourly forecast for temperature, relative humidity, and 10m wind speed.
    openmeteo_hourly_params = "temperature_2m,relative_humidity_2m,windspeed_10m"

    raw_data_dir = "data/raw"
    os.makedirs(raw_data_dir, exist_ok=True) # Ensure data/raw directory exists
    output_cpcb_path = os.path.join(raw_data_dir, "cpcb_live_with_weather.csv") # New combined CSV

    pm25_records = []

    print("Fetching PM2.5 data from OpenAQ...")
    try:
        openaq_res = requests.get(openaq_url, params=openaq_params, timeout=30) # 30-second timeout
        openaq_res.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        openaq_data = openaq_res.json()

        for item in openaq_data.get('results', []):
            # Basic validation to ensure required keys exist
            if all(k in item and 'coordinates' in item and 'latitude' in item['coordinates'] and 
                   'longitude' in item['coordinates'] and 'date' in item and 'utc' in item['date'] and
                   'value' in item for k in ['value', 'coordinates', 'date']):
                pm25_records.append({
                    "lat": item['coordinates']['latitude'],
                    "lon": item['coordinates']['longitude'],
                    "timestamp": item['date']['utc'],
                    "PM2.5": item['value'],
                    "location_name": item.get('location', 'Unknown'), # Station name
                    "city": item.get('city', 'Unknown') # City name
                })

        df_pm25 = pd.DataFrame(pm25_records)
        df_pm25['timestamp'] = pd.to_datetime(df_pm25['timestamp'], utc=True) # Convert to UTC datetime

        if df_pm25.empty:
            print("No PM2.5 data fetched from OpenAQ. Returning empty DataFrame.")
            return pd.DataFrame()

        # Sort by timestamp and keep only the latest reading for each unique location (lat, lon)
        # This is important to avoid duplicate entries for the same station.
        df_pm25 = df_pm25.sort_values(by='timestamp', ascending=False)
        df_pm25 = df_pm25.drop_duplicates(subset=['lat', 'lon']).reset_index(drop=True)

        print(f"Fetched {len(df_pm25)} unique PM2.5 records from OpenAQ.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching PM2.5 data from OpenAQ: {e}")
        return pd.DataFrame()

    # --- Fetch Weather Data for each unique PM2.5 location ---
    print("Fetching meteorological data from Open-Meteo for each PM2.5 location...")
    weather_data_list = []

    # Iterate through each unique PM2.5 location to get its weather forecast
    for idx, row in df_pm25.iterrows():
        lat, lon = row['lat'], row['lon']

        # Open-Meteo has rate limits (e.g., 600 calls/min, 10,000 calls/day for free tier).
        # Add a small delay to avoid hitting limits if you have many locations.
        if idx % 50 == 0 and idx > 0: # Print progress every 50 locations
            print(f"  Processed weather for {idx} locations...")
            time.sleep(0.5) # Pause for half a second

        try:
            # Fetch hourly forecast for the specific lat/lon
            weather_url = f"{openmeteo_base_url}?latitude={lat}&longitude={lon}&hourly={openmeteo_hourly_params}&timezone=auto"
            weather_res = requests.get(weather_url, timeout=10)
            weather_res.raise_for_status()
            weather_data = weather_res.json()

            hourly_times = weather_data['hourly']['time']
            hourly_temps = weather_data['hourly']['temperature_2m']
            hourly_humidity = weather_data['hourly']['relative_humidity_2m']
            hourly_wind = weather_data['hourly']['windspeed_10m']

            weather_df_hourly = pd.DataFrame({
                'timestamp': pd.to_datetime(hourly_times, utc=True),
                'temperature': hourly_temps,
                'humidity': hourly_humidity,
                'wind_speed': hourly_wind
            })

            # Find the weather record closest in time to the PM2.5 reading's timestamp
            # This is crucial for aligning real-time data.
            pm25_dt = row['timestamp']

            # Calculate time difference and find the closest weather forecast entry
            weather_df_hourly['time_diff'] = (weather_df_hourly['timestamp'] - pm25_dt).abs()
            closest_weather_row = weather_df_hourly.loc[weather_df_hourly['time_diff'].idxmin()]

            weather_data_list.append({
                "lat": lat,
                "lon": lon,
                "temperature": closest_weather_row['temperature'],
                "humidity": closest_weather_row['humidity'],
                "wind_speed": closest_weather_row['wind_speed']
            })

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching weather for ({lat}, {lon}): {e}")
        except KeyError as e:
            print(f"  KeyError in Open-Meteo response for ({lat}, {lon}): {e}. Response: {weather_res.json()}")
        except Exception as e:
            print(f"  An unexpected error occurred while fetching weather for ({lat}, {lon}): {e}")

    df_weather = pd.DataFrame(weather_data_list)

    if df_weather.empty:
        print("No weather data fetched. Filling weather features with NaN.")
        df_final = df_pm25.copy()
        df_final['temperature'] = pd.NA
        df_final['humidity'] = pd.NA
        df_final['wind_speed'] = pd.NA
    else:
        # Merge PM2.5 data with weather data based on latitude and longitude
        # Use 'left' merge to keep all PM2.5 records, even if no matching weather was found
        df_final = pd.merge(df_pm25, df_weather, on=['lat', 'lon'], how='left')

    # Save the combined data (PM2.5 + Weather)
    df_final.to_csv(output_cpcb_path, index=False)
    print(f"Combined CPCB PM2.5 and Open-Meteo weather data saved to {output_cpcb_path}! Records: {len(df_final)}")
    return df_final

if __name__ == "__main__":
    print("Attempting to fetch live CPCB and weather data...")
    fetch_cpcb_and_weather_data()