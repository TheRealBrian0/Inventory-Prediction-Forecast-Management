"""Fallback forecasting utilities."""

from datetime import timedelta

import numpy as np
import pandas as pd


def forecast_demand_simple(train_data, periods=30):
    """Simple forecasting method using moving average and trend."""
    recent_demand = train_data['y'].tail(14).mean()

    if len(train_data) >= 7: #check if we hve 2 weeks worth of data to calculate trend
        week_avg = train_data['y'].tail(7).mean()
        prev_week_avg = train_data['y'].tail(14).head(7).mean()
        trend = (week_avg - prev_week_avg) / 7 #trend per day or 'slope' calculation
    else:
        trend = 0

    last_date = train_data['ds'].max() #most recent date in df
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=periods) #creates 30 days of future dates from that date

    forecasts = []
    for i in range(periods):
        predicted = recent_demand + (trend * i) #y = mx + b formul
        predicted = predicted * np.random.uniform(0.9, 1.1) #keep randomness plus/minus 10
        forecasts.append(max(0, predicted)) #safety check to ensure no negative values

    forecast_df = pd.DataFrame({
        'ds': future_dates,
        'yhat': forecasts,
        'yhat_lower': [f * 0.85 for f in forecasts],
        'yhat_upper': [f * 1.15 for f in forecasts],
    })

    return forecast_df
