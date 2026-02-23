"""Prophet-based forecasting utilities."""

import warnings

from inventory_app.forecasting.fallback import forecast_demand_simple

warnings.filterwarnings('ignore')

PROPHET_AVAILABLE = False
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
    print('Using Prophet for time series forecasting')
except ImportError:
    try:
        from fbprophet import Prophet
        PROPHET_AVAILABLE = True
        print('Using fbprophet for time series forecasting')
    except ImportError:
        print('Warning: Prophet not available')


def forecast_demand_prophet(train_data, periods=30):
    """Forecast demand using Prophet, or fallback if unavailable."""
    if not PROPHET_AVAILABLE:
        return forecast_demand_simple(train_data, periods)

    try:
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        model.fit(train_data)

        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)

        return forecast
    except Exception as e:
        print(f'Prophet forecasting error: {e}')
        return forecast_demand_simple(train_data, periods)
