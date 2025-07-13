print(">>> ✅ Running the correct app.py!")


from pathlib import Path
import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from trends_util import fetch_trend_data

# Clear Streamlit cache once
try:
    from streamlit.runtime.caching import clear_cache
    clear_cache()
    print("✅ Streamlit cache cleared from code")
except Exception as e:
    print(f"⚠️ Could not clear cache programmatically: {e}")

st.set_page_config(page_title="TrendTrack AI", layout="wide")

NEW_PARTS_CSV = "new_parts.csv"

# Create a CSV file if it doesn't exist
if not Path(NEW_PARTS_CSV).exists():
    empty_df = pd.DataFrame(columns=[
        "product_id", "product_name", "sales", "date", "forecast",
        "anomaly", "z_score", "rolling_mean", "rolling_std"
    ])
    empty_df.to_csv(NEW_PARTS_CSV, index=False)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Forecasts", "Events/Logs", "Settings"])
st.sidebar.markdown("👋 Sidebar loaded successfully")  # Debug check

# Initialize session state with persistent parts
if "new_parts" not in st.session_state:
    st.session_state.new_parts = pd.read_csv(NEW_PARTS_CSV)
    if not st.session_state.new_parts.empty and "date" in st.session_state.new_parts.columns:
        st.session_state.new_parts["date"] = pd.to_datetime(st.session_state.new_parts["date"])

# Load forecasted sales data
@st.cache_data
def load_data():
    return pd.read_csv("forecast_output.csv") if Path("forecast_output.csv").exists() else pd.DataFrame()

df = load_data()

# Merge with saved new parts
if not st.session_state.new_parts.empty:
    df = pd.concat([df, st.session_state.new_parts], ignore_index=True)

# Add Part Form
with st.sidebar.expander("➕ Add New Part"):
    with st.form("add_part_form"):
        new_sku = st.text_input("SKU / Part ID")
        new_name = st.text_input("Part Name")
        new_qty = st.number_input("Stock Level", min_value=0, step=1)
        submit = st.form_submit_button("Add Part")

    if submit:
        new_row = pd.DataFrame([{
            "product_id": new_sku,
            "product_name": new_name,
            "sales": new_qty,
            "date": pd.to_datetime("today").normalize(),
            "forecast": 0,
            "anomaly": False,
            "z_score": 0,
            "rolling_mean": None,
            "rolling_std": None
        }])
        st.session_state.new_parts = pd.concat([st.session_state.new_parts, new_row], ignore_index=True)
        st.session_state.new_parts.to_csv(NEW_PARTS_CSV, index=False)
        st.success(f"✅ Part {new_sku} added!")

# Main Page Layout
if page == "Dashboard":
    st.title("📦 TrendTrack AI Inventory Dashboard")
    st.subheader("SKU Overview")

    if df.empty:
        st.warning("No data loaded. Run the forecast model to generate results.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total SKUs Tracked", df['product_id'].nunique())
        col2.metric("Detected Anomalies", int(df['anomaly'].sum()))
        col3.metric("Average Forecasted Sales", round(df['forecast'].mean(), 2))
        col4.metric("At-Risk Stockouts", df[df['forecast'] < df['sales']].shape[0])

        st.dataframe(df.head(20), use_container_width=True)

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

        st.subheader("Google Trends for SKU: CTS-INT-58")
        trends_df = fetch_trend_data("CTS-INT-58")
        if not trends_df.empty:
            fig2, ax2 = plt.subplots(figsize=(10, 3))
            ax2.plot(trends_df.index, trends_df["CTS-INT-58"], color="green", label="Search Interest")
            ax2.set_title("Search Interest (Google Trends)")
            ax2.set_xlabel("Date")
            ax2.set_ylabel("Interest")
            ax2.grid(True)
            st.pyplot(fig2)
        else:
            st.info("No Google Trends data available for this term.")

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
