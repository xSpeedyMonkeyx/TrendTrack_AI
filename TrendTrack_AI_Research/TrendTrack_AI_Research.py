import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
import os

#Simulate inventory sales data
np.random.seed(42)
date_range = pd.date_range(start="2024-01-01", end="2024-06-30", freq="D")

sales_data = pd.DataFrame({
    "date": date_range,
    "product_id": "CTS-INT-58", #placeholder
    "sales": np.random.poisson(lam=10, size=len(date_range))
})

#Prophet Forecasting Model Prep
prophet_df = sales_data.rename(columns={"date": "ds", "sales": "y"})[["ds", "y"]]

model = Prophet(daily_seasonality=True)
model.fit(prophet_df)

future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

#Anomaly Detection with rolling Z-Score
window = 14
sales_data["rolling_mean"] = sales_data["sales"].rolling(window=window).mean()
sales_data["rolling_std"] = sales_data["sales"].rolling(window=window).std()
sales_data["z_score"] = (sales_data["sales"] - sales_data["rolling_mean"]) / sales_data["rolling_std"]
sales_data["anomaly"] = sales_data["z_score"].abs() > 2

#Merge forecast with sales data
forecast_trimmed = forecast[["ds", "yhat"]].rename(columns={"ds": "date", "yhat": "forecast"})
final_df = pd.merge(sales_data, forecast_trimmed, on="date", how="left")

#Export results
output_path = "forecast_output.csv"
final_df.to_csv(output_path, index=False)
print(f"✅ Forecast with anomalies exported to {output_path}")

#Plot Forecast vs Actual
plt.figure(figsize=(10, 5))
plt.plot(final_df["date"], final_df["sales"], label="Actual Sales", color="blue")
plt.plot(final_df["date"], final_df["forecast"], label="Forecast", color="orange")
plt.scatter(final_df.loc[final_df["anomaly"], "date"], 
            final_df.loc[final_df["anomaly"], "sales"], 
            color='red', label="Anomaly", zorder=5)
plt.legend()
plt.title("Sales vs Forecast with Anomalies")
plt.xlabel("Date")
plt.ylabel("Units Sold")
plt.grid(True)
plt.tight_layout()
plt.savefig("forecast_plot.png")
plt.show()