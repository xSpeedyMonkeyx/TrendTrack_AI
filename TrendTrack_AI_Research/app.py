
from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="TrendTrack AI", layout="wide")

#sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Forecasts", "Events/Logs", "Settings"])

#load mock data
@st.cache_data
def load_data():
    return pd.read_csv("forecast_output.csv") if Path("forecast_output.csv").exists() else pd.DataFrame()

df = load_data()

if page == "Dashboard":
    st.title("📦 TrendTrack AI Inventory Dashboard")
    st.subheader("SKU Overview")

    if df.empty:
        st.warning("No data loaded. Run the forecast model to generate results.")
    else:
        #summary cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total SKUs Tracked", df['product_id'].nunique())
        col2.metric("Detected Anomalies", int(df['anomaly'].sum()))
        col3.metric("Average Forecasted Sales", round(df['forecast'].mean(), 2))
        col4.metric("At-Risk Stockouts", df[df['forecast'] < df['sales']].shape[0])

        #data table
        st.dataframe(df.head(20), use_container_width=True)

        #plot
        st.subheader("Forecast vs Actual Sales")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df["date"], df["sales"], label="Actual Sales", color="blue")
        ax.plot(df["date"], df["forecast"], label="Forecast", color="orange")
        anomaly_dates = df.loc[df["anomaly"], "date"]
        anomaly_sales = df.loc[df["anomaly"], "sales"]
        ax.scatter(anomaly_dates, anomaly_sales, color="red", label="Anomaly", zorder=5)
        ax.set_xlabel("Date")
        ax.set_ylabel("Units Sold")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

elif page == "Forecasts":
    st.title("🔮 Forecast Output")
    st.text("Future implementation: Allow SKU selection and forecast window tuning.")

elif page == "Events/Logs":
    st.title("📋 Events and Anomaly Logs")
    if not df.empty:
        logs = df[df["anomaly"]][["date", "product_id", "sales", "forecast", "z_score"]]
        st.dataframe(logs)

elif page == "Settings":
    st.title("⚙️ Settings")
    st.text("Placeholder: Add model retraining, thresholds, and Google Trends settings.")
