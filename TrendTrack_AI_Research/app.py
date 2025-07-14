from pathlib import Path
import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from trends_util import fetch_trend_data

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

# ADD PART FORM
st.sidebar.subheader("➕ Add New Part")
with st.sidebar.form("add_part_form"):
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

# --- CSV UPLOAD ---
st.sidebar.subheader("📁 Upload CSV File")
uploaded_csv = st.sidebar.file_uploader("Upload a CSV of parts", type=["csv"])

if uploaded_csv:
    uploaded_df = pd.read_csv(uploaded_csv)
    st.sidebar.markdown("### Map CSV Columns")
    sku_col = st.sidebar.selectbox("Select SKU Column", uploaded_df.columns)
    name_col = st.sidebar.selectbox("Select Part Name Column", uploaded_df.columns)
    qty_col = st.sidebar.selectbox("Select Stock Level Column", uploaded_df.columns)

    if st.sidebar.button("Add Parts from CSV"):
        imported_rows = uploaded_df[[sku_col, name_col, qty_col]].copy()
        imported_rows.columns = ["product_id", "product_name", "sales"]
        imported_rows["date"] = pd.to_datetime("today").normalize()
        imported_rows["forecast"] = 0
        imported_rows["anomaly"] = False
        imported_rows["z_score"] = 0
        imported_rows["rolling_mean"] = None
        imported_rows["rolling_std"] = None

        st.session_state.new_parts = pd.concat([st.session_state.new_parts, imported_rows], ignore_index=True)
        st.session_state.new_parts.to_csv(NEW_PARTS_CSV, index=False)
        st.success(f"✅ {len(imported_rows)} parts added from CSV!")
        st.dataframe(imported_rows)

# MAIN PAGE LOGIC
if page == "Dashboard":
    st.title("📦 TrendTrack AI Inventory Dashboard")
    st.subheader("SKU Overview")

    if df.empty:
        st.warning("No data loaded. Run the forecast model to generate results.")
    else:
        # Summary Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total SKUs Tracked", df['product_id'].nunique())
        col2.metric("Detected Anomalies", int(df['anomaly'].sum()))
        col3.metric("Average Forecasted Sales", round(df['forecast'].mean(), 2))
        col4.metric("At-Risk Stockouts", df[df['forecast'] < df['sales']].shape[0])

        # Data Table
        st.dataframe(df.head(20), use_container_width=True)

        # Sales vs Forecast Plot
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

        # Google Trends Plot
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
