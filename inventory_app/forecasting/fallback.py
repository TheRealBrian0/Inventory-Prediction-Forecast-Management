"""Fallback forecasting utilities."""

from datetime import timedelta

import numpy as np
import pandas as pd


def forecast_demand_simple(train_data, periods=30):
    """Simple forecasting method using moving average and trend."""
    recent_demand = train_data['y'].tail(14).mean()

    if len(train_data) >= 7:
        week_avg = train_data['y'].tail(7).mean()
        prev_week_avg = train_data['y'].tail(14).head(7).mean()
        trend = (week_avg - prev_week_avg) / 7
    else:
        trend = 0

    last_date = train_data['ds'].max()
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=periods)

    forecasts = []
    for i in range(periods):
        predicted = recent_demand + (trend * i)
        predicted = predicted * np.random.uniform(0.9, 1.1)
        forecasts.append(max(0, predicted))

    forecast_df = pd.DataFrame({
        'ds': future_dates,
        'yhat': forecasts,
        'yhat_lower': [f * 0.85 for f in forecasts],
        'yhat_upper': [f * 1.15 for f in forecasts],
    })

    return forecast_df
