import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib
import os

def train_pm_model():
    """Loads processed data, trains a Random Forest model, and saves it."""

    processed_data_path = "data/processed/merged_data.csv"
    model_output_path = "models/random_forest.pkl"
    validation_report_path = "outputs/validation_report.csv"

    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(validation_report_path), exist_ok=True)

    if not os.path.exists(processed_data_path):
        print(f"Error: {processed_data_path} not found. Please run src/process_satellite_data.py first.")
        return

    df = pd.read_csv(processed_data_path)

    # Define features (X) and target (y)
    required_columns = ["AOD", "temperature", "humidity", "wind_speed", "PM2.5"]
    if not all(col in df.columns for col in required_columns):
        print(f"Missing required columns in data. Found: {df.columns.tolist()}")
        print(f"Required: {required_columns}")
        missing_cols = [col for col in required_columns if col not in df.columns]
        print(f"Specifically missing: {missing_cols}")
        print("Please ensure src/process_satellite_data.py correctly generates these features.")
        return

    # Handle potential NaNs by dropping rows for training if any of the required features are missing
    df_cleaned = df.dropna(subset=required_columns).copy()

    if df_cleaned.empty:
        print("No complete data records available for training after dropping NaNs. Check previous data processing steps.")
        return

    X = df_cleaned[["AOD", "temperature", "humidity", "wind_speed"]]
    y = df_cleaned["PM2.5"]

    # Split data into training and testing sets (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    if X_train.empty or X_test.empty:
        print("Not enough data to split into training and testing sets. Need more records in merged_data.csv.")
        return

    # Initialize and train the Random Forest Regressor model
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    print("Training Random Forest model...")
    model.fit(X_train, y_train)
    print("Model training complete.")

    # Make predictions on the test set to evaluate performance
    preds = model.predict(X_test)

    # Calculate Mean Absolute Error (MAE)
    mae = mean_absolute_error(y_test, preds)
    print(f"Model Mean Absolute Error (MAE): {mae:.2f}")

    # Save the trained model to disk using joblib
    joblib.dump(model, model_output_path)
    print(f"Trained model saved to {model_output_path}")

    # Save actual vs. predicted values for a validation report CSV
    df_result = pd.DataFrame({
        "actual_PM": y_test,
        "predicted_PM": preds
    })
    df_result.to_csv(validation_report_path, index=False)
    print(f"Validation report saved to {validation_report_path}")

if __name__ == "__main__":
    print("Starting model training process...")
    train_pm_model()