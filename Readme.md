# Satellite-Hybrid PM2.5 Monitor

## Overview

The Satellite-Hybrid PM2.5 Monitor is a Python-based application designed to estimate surface-level PM2.5 (particulate matter with a diameter of 2.5 micrometers or less) concentrations across India. It achieves this by intelligently combining satellite-derived Aerosol Optical Depth (AOD) data, meteorological reanalysis data, and ground-based PM2.5 measurements. Leveraging machine learning algorithms, the application generates high-resolution spatial PM2.5 maps, providing valuable air quality information even in regions with limited or no ground-based monitoring stations. An interactive Streamlit dashboard allows users to visualize, explore, and analyze pollution patterns.

## Key Features

*   **Nationwide PM2.5 Estimation:** Employs INSAT-3D/3DR/3DS AOD data to predict PM2.5 levels across India.
*   **Hybrid Data Fusion:** Integrates satellite AOD, MERRA-2 meteorological reanalysis, and CPCB ground measurements for enhanced accuracy and robustness.
*   **High-Resolution Spatial Maps:** Generates detailed and visually informative maps of PM2.5 concentrations at a high spatial resolution.
*   **Interactive Streamlit Dashboard:** Offers a user-friendly web interface for exploring data, visualizing predictions, and analyzing trends.
*   **Machine Learning Core:** Utilizes a Random Forest Regressor (with options for XGBoost or LightGBM) for accurate PM2.5 estimation.
*   **Open-Source and Modular:** Designed for easy deployment, customization, and extension.

## Technologies Used

*   **Python (>=3.7):** The primary programming language.
*   **pandas:** Data manipulation and analysis with DataFrames.
*   **numpy:** Numerical computing and array operations.
*   **scikit-learn:** Machine learning algorithms and model evaluation.
*   **xarray:** Handling multi-dimensional arrays for satellite and meteorological data.
*   **netCDF4:** Reading and writing NetCDF files (common for scientific data).
*   **matplotlib, seaborn:** Static data visualization.
*   **folium, cartopy:** Interactive map creation and geospatial visualization.
*   **geopandas, shapely:** Geospatial data processing and analysis.
*   **Streamlit:** Building the interactive web application.
*   **joblib:** Saving and loading trained machine learning models.

## Data Sources

*   **Satellite AOD:** INSAT-3D/3DR/3DS Aerosol Optical Depth data from MOSDAC ([https://www.mosdac.gov.in/](https://www.mosdac.gov.in/)).  Requires registration and data download.
*   **Ground PM2.5 Data:** Central Pollution Control Board (CPCB) data (obtained through official channels or potentially via OpenAQ API).
*   **Meteorological Data:** NASA's MERRA-2 reanalysis data, available through the GES DISC data portal.

## System Architecture

## Installation

1.  **Clone the repository:**
2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Data Acquisition and Preprocessing:** Download and preprocess data from MOSDAC (INSAT AOD), CPCB (Ground PM2.5), and NASA GES DISC (MERRA-2).  Detailed preprocessing scripts are provided in the `scripts/` directory.  **Note:** Access to some data sources may require registration or API keys.

2.  **Model Training:**

    ```bash
    python scripts/train_model.py --config config/model_config.yaml
    ```
    (Example:  Adjust the path to your training script and configuration file.)

3.  **Run the Streamlit Application:**

    ```bash
    streamlit run app.py
    ```

4.  **Access the Application:** Open your web browser and navigate to the URL provided by Streamlit (typically `http://localhost:8501`).

## Contributing

Contributions are highly encouraged! Please submit pull requests with clear descriptions of the changes, following the project's coding style and guidelines.
