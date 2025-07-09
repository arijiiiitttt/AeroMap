import os
import subprocess
import sys

def run_script(script_path):
    """Helper function to run a Python script."""
    print(f"\n--- Running: {script_path} ---")
    # Use sys.executable to ensure the script runs with the active virtual environment's python
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Errors from {script_path}:\n{result.stderr}")
    if result.returncode != 0:
        print(f"Script {script_path} failed with exit code {result.returncode}")
        sys.exit(1) # Exit if any script fails

if __name__ == "__main__":
    print("Starting the complete PM2.5 Estimation pipeline...")

    # Step 1: Fetch live ground and weather data
    run_script("src/fetch_data.py")

    # Step 2: Process satellite AOD data and merge with live data
    # IMPORTANT: Ensure you have manually downloaded INSAT AOD files into data/raw/INSAT_AOD/
    # before running this step!
    run_script("src/process_satellite_data.py")

    # Step 3: Train the Machine Learning Model
    run_script("src/train_model.py")

    # Step 4: Generate the PM2.5 Prediction Map
    run_script("src/predict_and_map.py")

    print("\n--- Backend pipeline completed successfully! ---")
    print("You can now launch the Streamlit dashboard: `streamlit run ui/app.py`")