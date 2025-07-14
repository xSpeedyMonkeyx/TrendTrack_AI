from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from trends_util import fetch_trend_data

st.set_page_config(page_title="TrendTrack AI", layout="wide")

NEW_PARTS_CSV = "new_parts.csv"

# Confirm CSV exists
if not Path(NEW_PARTS_CSV).exists():
    pd.DataFrame(columns=[
        "product_id", "product_name", "inventory", "date", "forecast",
        "anomaly", "z_score", "rolling_mean", "rolling_std"
    ]).to_csv(NEW_PARTS_CSV, index=False)

# Load persistent data
if "new_parts" not in st.session_state:
    st.session_state.new_parts = pd.read_csv(NEW_PARTS_CSV)
    if "date" in st.session_state.new_parts.columns:
        st.session_state.new_parts["date"] = pd.to_datetime(st.session_state.new_parts["date"])

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Forecasts", "Events/Logs", "Settings"])

# Add a Part Form
st.sidebar.subheader("➕ Add New Part")
with st.sidebar.form("add_part_form"):
    new_sku = st.text_input("SKU / Part ID")
    new_name = st.text_input("Part Name")
    new_qty = st.number_input("Inventory", min_value=0, step=1)
    submit = st.form_submit_button("Add Part")
if submit:
    new_row = pd.DataFrame([{
        "product_id": new_sku,
        "product_name": new_name,
        "inventory": new_qty,
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

# Upload CSV Option
st.sidebar.subheader("📁 Upload CSV File")
uploaded_csv = st.sidebar.file_uploader("Upload a CSV of parts", type=["csv"])
if uploaded_csv:
    uploaded_df = pd.read_csv(uploaded_csv)
    st.sidebar.markdown("### Map CSV Columns")
    sku_col = st.sidebar.selectbox("Select SKU Column", uploaded_df.columns)
    name_col = st.sidebar.selectbox("Select Part Name Column", uploaded_df.columns)
    qty_col = st.sidebar.selectbox("Select Inventory Column", uploaded_df.columns)
    if st.sidebar.button("Add Parts from CSV"):
        imported = uploaded_df[[sku_col, name_col, qty_col]].copy()
        imported.columns = ["product_id", "product_name", "inventory"]
        imported["date"] = pd.to_datetime("today").normalize()
        imported["forecast"] = 0
        imported["anomaly"] = False
        imported["z_score"] = 0
        imported["rolling_mean"] = None
        imported["rolling_std"] = None
        st.session_state.new_parts = pd.concat([st.session_state.new_parts, imported], ignore_index=True)
        st.session_state.new_parts.to_csv(NEW_PARTS_CSV, index=False)
        st.success(f"✅ {len(imported)} parts added from CSV!")

# Dashboard Layout
if page == "Dashboard":
    st.title("📦 TrendTrack AI Inventory Dashboard")
    df = st.session_state.new_parts.copy()

    if df.empty:
        st.warning("No data available. Add parts or upload CSV.")
    else:
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total SKUs Tracked", df['product_id'].nunique())
        col2.metric("Detected Anomalies", int(df['anomaly'].sum()))
        col3.metric("Average Forecasted Sales", round(df['forecast'].mean(), 2))
        col4.metric("At-Risk Stockouts", df[df['forecast'] < df['inventory']].shape[0])

        # Inventory Overview
        st.subheader("📋 Inventory Overview")
        selected = st.data_editor(df[["product_id", "product_name", "inventory", "forecast", "date"]].rename(columns={
            "product_id": "SKU",
            "product_name": "Product Name",
            "inventory": "Quantity",
            "forecast": "Forecast",
            "date": "Date"
        }), num_rows="dynamic", use_container_width=True, hide_index=True)

        # Get selected SKU from table when clicked
        selected_part = None
        if len(selected["SKU"]) > 0:
            last_clicked = selected["SKU"].iloc[-1]
            selected_part = df[df["product_id"] == last_clicked].iloc[0]

        if selected_part is not None:
            st.subheader("🛠️ Manage Selected Part")
            new_qty = st.number_input(f"Adjust Inventory for {selected_part['product_id']}", value=int(selected_part["inventory"]), step=1, key="adjust_qty")
            col_a, col_b = st.columns([1, 1])
            if col_a.button("Update Inventory"):
                st.session_state.new_parts.loc[st.session_state.new_parts["product_id"] == selected_part["product_id"], "inventory"] = new_qty
                st.session_state.new_parts.to_csv(NEW_PARTS_CSV, index=False)
                st.success(f"Inventory updated for {selected_part['product_id']}")

            if col_b.button("❌ Delete SKU"):
                st.session_state.new_parts = st.session_state.new_parts[st.session_state.new_parts["product_id"] != selected_part["product_id"]]
                st.session_state.new_parts.to_csv(NEW_PARTS_CSV, index=False)
                st.success(f"SKU {selected_part['product_id']} deleted!")

            # Google Trends Search/Information
            st.subheader("🔍 Google Trends")
            trends_sku = fetch_trend_data(selected_part["product_id"])
            trends_name = fetch_trend_data(selected_part["product_name"])

            if not trends_sku.empty or not trends_name.empty:
                fig, ax = plt.subplots(figsize=(10, 4))
                if not trends_sku.empty:
                    ax.plot(trends_sku.index, trends_sku[selected_part["product_id"]], label=selected_part["product_id"], color="blue")
                if not trends_name.empty:
                    ax.plot(trends_name.index, trends_name[selected_part["product_name"]], label=selected_part["product_name"], color="green")
                ax.set_title("Search Interest (Google Trends)")
                ax.set_xlabel("Month")
                ax.set_ylabel("Search Interest Score (0–100)")
                ax.legend()
                ax.grid(True)
                ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b %Y"))
                st.pyplot(fig)
            else:
                st.info(f"No Google Trends data found for {selected_part['product_id']}.")

elif page == "Forecasts":
    st.title("🔮 Forecast Output")
    st.info("Placeholder for future forecasting functionality.")

elif page == "Events/Logs":
    st.title("📋 Events and Anomaly Logs")
    df = st.session_state.new_parts
    if not df.empty:
        logs = df[df["anomaly"]][["date", "product_id", "inventory", "forecast", "z_score"]]
        st.dataframe(logs)

elif page == "Settings":
    st.title("⚙️ Settings")
    st.text("Configuration options for retraining and thresholds coming soon.")
