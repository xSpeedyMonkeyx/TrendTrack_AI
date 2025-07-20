from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from trends_util import fetch_trend_data
import json
import numpy as np

st.set_page_config(page_title="TrendTrack AI", layout="wide")

NEW_PARTS_CSV = "new_parts.csv"
SETTINGS_FILE = "settings.json"

# Confirm new_parts.csv exists
if not Path(NEW_PARTS_CSV).exists():
    pd.DataFrame(columns=[
        "product_id", "product_name", "inventory", "date", "forecast",
        "anomaly", "z_score", "rolling_mean", "rolling_std", "category"
    ]).to_csv(NEW_PARTS_CSV, index=False)

# Load part data
if "new_parts" not in st.session_state:
    st.session_state.new_parts = pd.read_csv(NEW_PARTS_CSV)
    if "category" not in st.session_state.new_parts.columns:
        st.session_state.new_parts["category"] = "Uncategorized"
    if "date" in st.session_state.new_parts.columns:
        st.session_state.new_parts["date"] = pd.to_datetime(st.session_state.new_parts["date"])

# Load settings
if not Path(SETTINGS_FILE).exists():
    default_settings = {"z_threshold": 3.0}
    with open(SETTINGS_FILE, "w") as f:
        json.dump(default_settings, f)
else:
    with open(SETTINGS_FILE, "r") as f:
        default_settings = json.load(f)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Forecasts", "Events/Logs", "Settings"])

# Add New Part Form
st.sidebar.subheader("➕ Add New Part")
with st.sidebar.form("add_part_form"):
    new_sku = st.text_input("SKU / Part ID")
    new_name = st.text_input("Part Name")
    new_qty = st.number_input("Inventory", min_value=0, step=1)
    new_category = st.text_input("Category")
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
        "rolling_std": None,
        "category": new_category
    }])
    st.session_state.new_parts = pd.concat([st.session_state.new_parts, new_row], ignore_index=True)
    st.session_state.new_parts.to_csv(NEW_PARTS_CSV, index=False)
    st.success(f"✅ Part {new_sku} added!")

# CSV Upload Option
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
        imported["category"] = "Uncategorized"
        st.session_state.new_parts = pd.concat([st.session_state.new_parts, imported], ignore_index=True)
        st.session_state.new_parts.to_csv(NEW_PARTS_CSV, index=False)
        st.success(f"✅ {len(imported)} parts added from CSV!")

        st.sidebar.markdown("---")
st.sidebar.markdown("#### 🚨 Danger Zone: Delete All Parts")
st.sidebar.warning("This will permanently delete all SKU's from your inventory.")

delete_confirm = st.sidebar.text_input("Type 'confirm' to enable delete", key="delete_all_confirm")
delete_clicked = st.sidebar.button("🗑️ Delete ALL SKU's", type="primary")

if delete_clicked:
    if delete_confirm.strip().lower() == "confirm":
        st.session_state.new_parts = pd.DataFrame(columns=[
            "product_id", "product_name", "inventory", "date", "forecast",
            "anomaly", "z_score", "rolling_mean", "rolling_std"
        ])
        st.session_state.new_parts.to_csv(NEW_PARTS_CSV, index=False)
        st.sidebar.success("✅ All SKU's have been deleted")
    else:
        st.sidebar.error("❌ Type 'confirm' to proceed with deleting all SKU's")

# Dashboard
if page == "Dashboard":
    st.title("📦 TrendTrack AI Inventory Dashboard")
    df = st.session_state.new_parts.copy()

    def estimate_stockout_date(row):
        if row["forecast"] <= 0:
            return "N/A"
        days_left = row["inventory"] / row["forecast"]
        return (pd.to_datetime("today") + pd.Timedelta(days=days_left)).strftime("%Y-%m-%d")

    def suggest_reorder_qty(row):
        needed = row["forecast"] * 14
        return max(int(round(needed - row["inventory"])), 0) if row["forecast"] > 0 else 0

    if not df.empty:
        df["stockout_date"] = df.apply(estimate_stockout_date, axis=1)
        df["reorder_qty"] = df.apply(suggest_reorder_qty, axis=1)
    else:
        df["stockout_date"] = []
        df["reorder_qty"] = []

    if df.empty:
        st.warning("No data available.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total SKUs Tracked", df['product_id'].nunique())
        col2.metric("Detected Anomalies", int(df['anomaly'].sum()))
        col3.metric("Avg Forecasted Sales", round(df['forecast'].mean(), 2))
        col4.metric("At-Risk Stockouts", df[df['forecast'] < df['inventory']].shape[0])

        #Category Filter
        with st.expander("🔍 Filter Inventory by Category", expanded=False):
            unique_categories = df["category"].dropna().unique()
            if len(unique_categories) > 0:
                selected_category = st.selectbox("Select Category", unique_categories)
                if st.button("Apply Filter"):
                    st.session_state.filtered_df = df[df["category"] == selected_category]
                if st.button("Clear Filter"):
                    st.session_state.pop("filtered_df", None)
            else:
                st.write("No categories available.")

        source_df = st.session_state.get("filtered_df", df)

        st.subheader("📋 Inventory Overview")
        selected = st.data_editor(
            source_df[["product_id", "product_name", "inventory", "forecast", "stockout_date", "reorder_qty", "date"]].rename(columns={
                "product_id": "SKU",
                "product_name": "Product Name",
                "inventory": "Quantity",
                "forecast": "Forecast",
                "stockout_date": "Est. Stockout",
                "reorder_qty": "Reorder Qty",
                "date": "Date"
            }), use_container_width=True, hide_index=True
        )

        source_df["sku_display"] = source_df["product_id"] + " — " + source_df["product_name"]
        display_to_sku = dict(zip(source_df["sku_display"], source_df["product_id"]))
        selected_display = st.selectbox("Select a SKU", source_df["sku_display"])
        selected_sku = display_to_sku[selected_display]
        selected_part = df[df["product_id"] == selected_sku].iloc[0]

        st.subheader("🛠️ Manage Selected Part")
        new_qty = st.number_input(f"Adjust Inventory for {selected_part['product_id']}", value=int(selected_part["inventory"]), step=1)
        col_a, col_b = st.columns(2)
        if col_a.button("Update Inventory"):
            st.session_state.new_parts.loc[
                st.session_state.new_parts["product_id"] == selected_part["product_id"], "inventory"
            ] = new_qty
            st.session_state.new_parts.to_csv(NEW_PARTS_CSV, index=False)
            st.success("Inventory updated.")
        if col_b.button("❌ Delete SKU"):
            st.session_state.new_parts = st.session_state.new_parts[
                st.session_state.new_parts["product_id"] != selected_part["product_id"]
            ]
            st.session_state.new_parts.to_csv(NEW_PARTS_CSV, index=False)
            st.success("SKU deleted.")
                   

        st.subheader("📈 Inventory vs Google Trends")

        trends_sku = fetch_trend_data(selected_part["product_id"])
        trends_name = fetch_trend_data(selected_part["product_name"])
        inventory_history = df[df["product_id"] == selected_part["product_id"]].copy()

        if not trends_sku.empty or not trends_name.empty:
            inventory_history["date"] = pd.to_datetime(inventory_history["date"])
            inventory_history = inventory_history.sort_values("date")

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(inventory_history["date"], inventory_history["inventory"], label="Inventory", color="blue")

            if not trends_sku.empty:
                ax.plot(trends_sku.index, trends_sku[selected_part["product_id"]],
                        label=f"Search: {selected_part['product_id']}", color="green")
            if not trends_name.empty:
                ax.plot(trends_name.index, trends_name[selected_part["product_name"]],
                        label=f"Search: {selected_part['product_name']}", color="orange")

            ax.set_title("Inventory vs Google Trends")
            ax.set_xlabel("Date")
            ax.set_ylabel("Value")
            ax.legend()
            ax.grid(True)
            ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b %Y"))
            st.pyplot(fig)
        else:
            st.info(f"No Google Trends data found for: {selected_part['product_id']} or {selected_part['product_name']}")

# Forecasts
elif page == "Forecasts":
    st.title("🔮 Forecast Output (7-Day Moving Average)")

    df = st.session_state.new_parts.copy()
    if df.empty:
        st.warning("No parts data available.")
    else:
        unique_skus = df["product_id"].unique()
        selected_sku = st.selectbox("Choose SKU for Forecast View", unique_skus)
        sku_df = df[df["product_id"] == selected_sku].copy()
        sku_df["date"] = pd.to_datetime(sku_df["date"])
        sku_df = sku_df.sort_values("date")

        sku_df["7_day_ma"] = sku_df["inventory"].rolling(window=7, min_periods=1).mean()

        st.line_chart(
            sku_df.set_index("date")[["inventory", "7_day_ma"]],
            use_container_width=True,
            height=350
        )

        st.caption("Shows actual inventory and 7-day moving average forecast for trend tracking.")

# Events / Logs
elif page == "Events/Logs":
    st.title("📋 Anomaly Logs")
    df = st.session_state.new_parts
    if not df.empty:
        logs = df[df["anomaly"] == True][["date", "product_id", "product_name", "inventory", "forecast", "z_score"]]
        if not logs.empty:
            logs.to_csv("logs.csv", index=False)
            st.success("Anomalies exported to logs.csv")
            st.dataframe(logs)
        else:
            st.info("✅ No anomalies detected.")

# Settings 
elif page == "Settings":
    st.title("⚙️ Settings")
    st.subheader("Z-Score Threshold")
    new_threshold = st.slider("Set Z-Score Threshold", 1.0, 5.0, float(default_settings["z_threshold"]), 0.1)
    if new_threshold != default_settings["z_threshold"]:
        default_settings["z_threshold"] = new_threshold
        with open(SETTINGS_FILE, "w") as f:
            json.dump(default_settings, f)
        st.success("Threshold updated.")

    st.subheader("Manual Model Retraining")
    if st.button("Run Model Retraining"):
        st.success("✅ Model retraining triggered.")
