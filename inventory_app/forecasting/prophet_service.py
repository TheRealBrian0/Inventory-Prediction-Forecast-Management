"""Prophet-based forecasting utilities."""

import warnings
import logging
import sys
from inventory_app.forecasting.fallback import forecast_demand_simple

warnings.filterwarnings('ignore')

logger = logging.getLogger("inventory_app.forecasting.prophet_service")
logger.setLevel(logging.INFO)

PROPHET_AVAILABLE = False
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
    logger.info("Prophet engine detected: prophet")
except ImportError:
    try:
        from fbprophet import Prophet
        PROPHET_AVAILABLE = True
        logger.info("Prophet engine detected: fbprophet")
    except ImportError:
        logger.warning("Prophet not available; fallback forecasting will be used")


def forecast_demand_prophet(train_data, periods=30):
    """Forecast demand using Prophet, or fallback if unavailable."""
    if not PROPHET_AVAILABLE:
        logger.info("Forecast path=fallback reason=prophet_unavailable periods=%s", periods)
        return forecast_demand_simple(train_data, periods)

    try:
        logger.info("Forecast path=prophet periods=%s", periods)
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
            changepoint_range=0.8,
            n_changepoints=20,
            mcmc_samples=0,
        )
        model.fit(train_data)

        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)

        return forecast
    except Exception as e:
        logger.exception("Prophet forecasting error; switching to fallback: %s", e)
        return forecast_demand_simple(train_data, periods)
