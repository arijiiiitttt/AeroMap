import pandas as pd
import joblib
import matplotlib.pyplot as plt
import os

def generate_pm_map():
    """Loads data and trained model, makes predictions, and generates a PM2.5 map."""

    processed_data_path = "data/processed/merged_data.csv"
    model_path = "models/random_forest.pkl"
    map_output_path = "outputs/india_pm_map.png"

    os.makedirs(os.path.dirname(map_output_path), exist_ok=True)

    if not os.path.exists(processed_data_path):
        print(f"Error: {processed_data_path} not found. Please run src/process_satellite_data.py first.")
        return
    if not os.path.exists(model_path):
        print(f"Error: {model_path} not found. Please run src/train_model.py first.")
        return

    df = pd.read_csv(processed_data_path)
    model = joblib.load(model_path)

    # Make predictions using the trained model
    required_features = ["AOD", "temperature", "humidity", "wind_speed"]
    if not all(col in df.columns for col in required_features):
        print(f"Missing required feature columns in data for prediction. Found: {df.columns.tolist()}")
        print(f"Required: {required_features}")
        return

    # Drop rows with NaN in features before prediction, as model.predict does not handle NaNs
    df_for_prediction = df.dropna(subset=required_features).copy()

    if df_for_prediction.empty:
        print("No complete data records available for prediction after dropping NaNs. Map cannot be generated.")
        return

    df_for_prediction["predicted_PM"] = model.predict(df_for_prediction[required_features])

    # Create the scatter plot map
    plt.figure(figsize=(12, 8)) # Set figure size for better visualization
    scatter = plt.scatter(df_for_prediction["lon"], df_for_prediction["lat"], 
                          c=df_for_prediction["predicted_PM"], cmap='Reds', s=30, alpha=0.7)
    plt.colorbar(scatter, label="Predicted PM2.5 (µg/m³)") # Add a color bar legend
    plt.title("Predicted Surface-Level PM2.5 Across India")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid(True, linestyle='--', alpha=0.6) # Add a subtle grid

    # Set approximate geographical limits for India to focus the map
    plt.xlim(65, 100)  # Longitude range for India
    plt.ylim(5, 38)   # Latitude range for India

    plt.savefig(map_output_path) # Save the map as a PNG image
    print(f"PM2.5 prediction map generated and saved to {map_output_path}")
    plt.show() # Display the plot window (will close after you close it)

if __name__ == "__main__":
    print("Starting prediction and map generation...")
    generate_pm_map()