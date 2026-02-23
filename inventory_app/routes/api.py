"""API routes for inventory forecast data."""

from flask import Blueprint, current_app, jsonify

from inventory_app.data.loader import load_data
from inventory_app.data.preprocess import preprocess_data
from inventory_app.services.dashboard import get_all_products_forecast, get_dashboard_metrics

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/metrics')
def api_metrics():
    """API endpoint for dashboard metrics."""
    df = load_data(current_app.config['CSV_PATH'])
    df = preprocess_data(df)

    metrics = get_dashboard_metrics(
        df,
        periods=current_app.config['FORECAST_PERIODS'],
        store_id=current_app.config['DEFAULT_STORE_ID'],
    )

    return jsonify(metrics)


@api_bp.route('/all-forecasts')
def api_all_forecasts():
    """API endpoint for all product forecasts."""
    df = load_data(current_app.config['CSV_PATH'])
    df = preprocess_data(df)

    forecasts = get_all_products_forecast(
        df,
        periods=current_app.config['FORECAST_PERIODS'],
        store_id=current_app.config['DEFAULT_STORE_ID'],
    )

    return jsonify(forecasts)
