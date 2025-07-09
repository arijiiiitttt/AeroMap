import xarray as xr
import pandas as pd
import numpy as np
import os
import datetime
from scipy.spatial import cKDTree # For efficient nearest-neighbor search
import re # For regular expressions to parse filenames

def process_satellite_data():
    """
    Processes manually downloaded satellite AOD (INSAT) data and merges it
    with the live-fetched ground-based PM2.5 and meteorological data.

    This function assumes you have manually downloaded INSAT AOD data files
    (e.g., .nc, .nc4, .hdf) into the data/raw/INSAT_AOD/ directory.
    The exact file names and variable names might need adjustment based on
    what you download.
    """

    # --- Paths ---
    # This CSV now contains PM2.5 and weather data from fetch_data.py
    cpcb_and_weather_path = "data/raw/cpcb_live_with_weather.csv" 
    insat_aod_dir = "data/raw/INSAT_AOD/"

    processed_output_path = "data/processed/merged_data.csv"

    # Ensure output directory exists
    os.makedirs(os.path.dirname(processed_output_path), exist_ok=True)

    if not os.path.exists(cpcb_and_weather_path):
        print(f"Error: {cpcb_and_weather_path} not found. Please run src/fetch_data.py first.")
        return

    df_ground_and_weather = pd.read_csv(cpcb_and_weather_path)
    df_ground_and_weather['timestamp'] = pd.to_datetime(df_ground_and_weather['timestamp'], utc=True)

    all_aod_data = []

    # --- Process INSAT AOD Data ---
    print("\nProcessing INSAT AOD data from downloaded files...")
    insat_files = [f for f in os.listdir(insat_aod_dir) if f.endswith(('.nc', '.nc4', '.hdf'))]

    if not insat_files:
        print(f"No INSAT AOD files found in {insat_aod_dir}. Skipping AOD processing.")
        print("Please manually download INSAT-3D/3DR AOD data (e.g., Level 2) from MOSDAC and place them in data/raw/INSAT_AOD/.")
    else:
        for insat_file in insat_files:
            insat_file_path = os.path.join(insat_aod_dir, insat_file)
            try:
                with xr.open_dataset(insat_file_path) as ds_aod:
                    # >>> IMPORTANT: Inspect your downloaded INSAT file to find the correct AOD variable name <<<
                    # You can use `print(ds_aod)` or `ds_aod.info()` after opening to see variable names.
                    aod_var_name = 'AOD_550nm' # <<< Adjust this if your file has a different AOD variable name

                    # Also, check the names of latitude, longitude, and time dimensions/coordinates
                    lat_dim_name = 'latitude'  # Common: 'latitude', 'lat'
                    lon_dim_name = 'longitude' # Common: 'longitude', 'lon'
                    time_dim_name = 'time'     # Common: 'time', 'datetime', 't'

                    if aod_var_name in ds_aod.variables and \
                       lat_dim_name in ds_aod.dims and \
                       lon_dim_name in ds_aod.dims:

                        if time_dim_name in ds_aod.dims:
                             df_aod = ds_aod[[aod_var_name]].to_dataframe().reset_index()
                             df_aod = df_aod.rename(columns={
                                 aod_var_name: 'AOD', 
                                 lat_dim_name: 'lat', 
                                 lon_dim_name: 'lon', 
                                 time_dim_name: 'timestamp'
                             })
                        else:
                            # If no explicit 'time' dimension, attempt to infer from filename or use current time
                            print(f"Warning: '{time_dim_name}' dimension not found in {insat_file}. Attempting to infer timestamp from filename or use current time.")
                            df_aod = ds_aod[[aod_var_name]].to_dataframe().reset_index()
                            df_aod = df_aod.rename(columns={
                                aod_var_name: 'AOD', 
                                lat_dim_name: 'lat', 
                                lon_dim_name: 'lon'
                            })
                            # Example: Try to parse YYYYMMDD_HHMM from filename
                            time_match = re.search(r'(\d{8})_(\d{4})', insat_file)
                            if time_match:
                                date_str = time_match.group(1)
                                time_str = time_match.group(2)
                                df_aod['timestamp'] = pd.to_datetime(f"{date_str}{time_str}", format='%Y%m%d%H%M', errors='coerce', utc=True)
                            else:
                                # Fallback to current UTC time if parsing fails
                                df_aod['timestamp'] = pd.to_datetime(datetime.datetime.now(datetime.timezone.utc).isoformat(), utc=True) 
                            df_aod = df_aod.dropna(subset=['timestamp']) # Drop rows if timestamp parsing failed

                        df_aod['timestamp'] = pd.to_datetime(df_aod['timestamp'], utc=True)
                        all_aod_data.append(df_aod[['lat', 'lon', 'timestamp', 'AOD']])
                        print(f"Successfully processed AOD from {insat_file}.")
                    else:
                        print(f"Warning: AOD variable ('{aod_var_name}') or lat/lon dimensions ('{lat_dim_name}', '{lon_dim_name}') not found in {insat_file_path}. Please check the file structure using ds_aod.info().")
            except Exception as e:
                print(f"Error processing INSAT AOD file {insat_file}: {e}")

    # Combine all processed AOD data into a single DataFrame
    if not all_aod_data:
        print("No INSAT AOD data processed. Filling 'AOD' column with NaN in merged data.")
        df_merged = df_ground_and_weather.copy()
        df_merged['AOD'] = np.nan
    else:
        df_all_aod = pd.concat(all_aod_data, ignore_index=True)
        # Remove duplicate AOD entries for the same spatio-temporal point
        df_all_aod = df_all_aod.drop_duplicates(subset=['lat', 'lon', 'timestamp']).reset_index(drop=True)

        # --- Merge DataFrames using nearest neighbor (spatial and temporal) for AOD ---
        print("\nMerging ground+weather data with satellite AOD data using nearest neighbor...")

        # Prepare AOD data for KDTree search
        # Convert timestamps to float (seconds since epoch) for distance calculation in KDTree
        df_all_aod['time_float'] = df_all_aod['timestamp'].astype(np.int64) // 10**9 
        df_ground_and_weather['time_float'] = df_ground_and_weather['timestamp'].astype(np.int64) // 10**9

        # Define a scaling factor for time in the KDTree. This is critical!
        # It determines how much a time difference is "worth" compared to a spatial difference.
        # Example: If 1 degree lat/lon is ~111 km, and you want 1 day (86400 seconds) to be
        # equivalent to, say, 0.1 degrees of spatial distance, then time_scale_factor = 86400 / 0.1 = 864000.
        # Adjust this based on your data's temporal resolution and desired spatio-temporal proximity.
        time_scale_factor = 864000 

        aod_coords = df_all_aod[['lat', 'lon', 'time_float']].copy()
        aod_coords['time_float'] = aod_coords['time_float'] / time_scale_factor # Scale time for KDTree
        tree = cKDTree(aod_coords.values)

        # Find the nearest AOD point for each ground+weather point
        ground_query_coords = df_ground_and_weather[['lat', 'lon', 'time_float']].copy()
        ground_query_coords['time_float'] = ground_query_coords['time_float'] / time_scale_factor # Scale time

        # Query the KDTree for the nearest neighbor for each ground station
        distances, indices = tree.query(ground_query_coords.values)

        # Add AOD to the ground+weather data
        # Ensure 'AOD' column exists in df_all_aod before accessing
        if 'AOD' in df_all_aod.columns:
            df_ground_and_weather['AOD'] = df_all_aod.loc[indices, 'AOD'].values
        else:
            df_ground_and_weather['AOD'] = np.nan # If AOD column was somehow missing from processed sat data

        # Drop the temporary 'time_float' column
        df_merged = df_ground_and_weather.drop(columns=['time_float'])

    # Drop any rows where essential features are still NaN (e.g., if a data source was completely missing)
    # The 'PM2.5' is from OpenAQ, 'temperature', 'humidity', 'wind_speed' from Open-Meteo, 'AOD' from INSAT.
    required_final_columns = ['AOD', 'temperature', 'humidity', 'wind_speed', 'PM2.5']
    df_merged = df_merged.dropna(subset=required_final_columns)

    if df_merged.empty:
        print("No complete data records after merging all sources. Check individual data fetching/processing steps.")
        return

    # Standardize timestamp format for final CSV
    df_merged['timestamp'] = df_merged['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    df_merged.to_csv(processed_output_path, index=False)
    print(f"Final merged data (ground, weather, AOD) saved to {processed_output_path}! Number of records: {len(df_merged)}")

if __name__ == "__main__":
    print("Starting processing of satellite AOD data and merging with live fetched data...")
    process_satellite_data()