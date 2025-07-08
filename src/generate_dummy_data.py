import pandas as pd
import random
import os

def generate_dummy():
    """Generates dummy AOD, temperature, humidity, and wind speed data
    based on the fetched CPCB live data, then merges and saves it."""

    # Ensure raw and processed directories exist
    raw_data_dir = "data/raw"
    processed_data_dir = "data/processed"
    os.makedirs(raw_data_dir, exist_ok=True)
    os.makedirs(processed_data_dir, exist_ok=True)

    cpcb_path = os.path.join(raw_data_dir, "cpcb_live.csv")
    processed_output_path = os.path.join(processed_data_dir, "merged_data.csv")

    if not os.path.exists(cpcb_path):
        print(f"Error: {cpcb_path} not found. Please run src/fetch_data.py first.")
        return

    df = pd.read_csv(cpcb_path)

    # Generate dummy data based on the number of rows in the fetched CPCB data
    num_rows = len(df)
    df["AOD"] = [round(random.uniform(0.1, 1.2), 2) for _ in range(num_rows)]
    df["temperature"] = [round(random.uniform(20, 40), 1) for _ in range(num_rows)] # Celsius
    df["humidity"] = [round(random.uniform(30, 90), 1) for _ in range(num_rows)] # Percentage
    df["wind_speed"] = [round(random.uniform(1, 10), 1) for _ in range(num_rows)] # m/s

    # Important: ensure 'timestamp' is correctly formatted if you plan to use it for time series later
    # For now, it's just a column for merging (implicitly handled by Pandas if values match)
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%dT%H:%M:%SZ') # Standardize format

    df.to_csv(processed_output_path, index=False)
    print(f"Dummy AOD, temperature, humidity, and wind speed generated and merged with CPCB data.")
    print(f"Saved to: {processed_output_path}")

if __name__ == "__main__":
    print("Attempting to generate dummy data...")
    generate_dummy()