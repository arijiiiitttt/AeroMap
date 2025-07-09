import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="PM2.5 India Dashboard", layout="wide")

st.title("🛰️ AI-Powered PM2.5 Estimation Dashboard for India")

st.markdown("""
This dashboard provides an estimation of surface-level PM2.5 concentrations across India,
leveraging a combination of ground-based measurements (OpenAQ), satellite data (INSAT AOD - manually downloaded),
and meteorological forecast data (Open-Meteo).

**Note on Data:** Ground and weather data are fetched live. Satellite AOD data needs to be manually downloaded
and placed in `data/raw/INSAT_AOD/`. The data merging and spatial alignment use simplified methods for demonstration.
""")

# --- Display the Generated Map ---
map_image_path = "outputs/india_pm_map.png"
if os.path.exists(map_image_path):
    st.image(map_image_path, caption="Predicted Surface-Level PM2.5 Across India", use_column_width=True)
else:
    st.warning("PM2.5 map not found. Please ensure all previous data processing and model steps ran successfully:")
    st.info("1. `python src/fetch_data.py` (to get ground and weather data)")
    st.info("2. **Manually download** INSAT AOD data into `data/raw/INSAT_AOD/`")
    st.info("3. `python src/process_satellite_data.py` (to process and merge AOD data)")
    st.info("4. `python src/train_model.py` (to train the model)")
    st.info("5. `python src/predict_and_map.py` (to generate the map)")
    st.info("The map will appear here once generated.")

st.markdown("---") # Separator

# --- Show Model Validation ---
st.subheader("📊 Model Validation Report")
validation_report_path = "outputs/validation_report.csv"

if os.path.exists(validation_report_path):
    if st.checkbox("Show detailed validation results"):
        df_validation = pd.read_csv(validation_report_path)
        st.dataframe(df_validation.head()) # Show first few rows of the validation data

        # Plot actual vs. predicted PM2.5
        st.line_chart(df_validation[['actual_PM', 'predicted_PM']])
        st.markdown("This chart compares the actual ground-level PM2.5 measurements with the model's predictions on unseen data.")
else:
    st.info("Validation report not found. Please run `python src/train_model.py` first to generate model results.")

st.markdown("---")
st.info("Built with ❤️ for a cleaner India. Data integration uses simplified methods for demonstration.")