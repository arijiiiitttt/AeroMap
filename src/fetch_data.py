import requests
import pandas as pd
import os

def fetch_cpcb_data():
    """Fetches live PM2.5 measurements from OpenAQ API for India."""
    # OpenAQ API endpoint for PM2.5 measurements in India
    url = "https://api.openaq.org/v2/measurements?country=IN&limit=1000&parameter=pm25"

    try:
        res = requests.get(url, timeout=10) # Add a timeout for robustness
        res.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = res.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from OpenAQ: {e}")
        return pd.DataFrame() # Return empty DataFrame on error

    records = []
    for item in data.get('results', []): # Use .get() to safely access 'results'
        # Check if all required keys exist
        if all(k in item and 'coordinates' in item and 'latitude' in item['coordinates'] and 
               'longitude' in item['coordinates'] and 'date' in item and 'utc' in item['date'] for k in ['value']):
            records.append({
                "lat": item['coordinates']['latitude'],
                "lon": item['coordinates']['longitude'],
                "timestamp": item['date']['utc'],
                "PM2.5": item['value']
            })
        else:
            print(f"Skipping malformed record: {item}")


    df = pd.DataFrame(records)

    # Ensure the raw directory exists
    raw_data_dir = "data/raw"
    os.makedirs(raw_data_dir, exist_ok=True) # Creates dir if it doesn't exist

    output_path = os.path.join(raw_data_dir, "cpcb_live.csv")
    df.to_csv(output_path, index=False)
    print(f"Live CPCB data saved to {output_path}! Number of records: {len(df)}")
    return df

if __name__ == "__main__":
    # This block runs only when you execute this file directly
    print("Attempting to fetch live CPCB data...")
    fetch_cpcb_data()