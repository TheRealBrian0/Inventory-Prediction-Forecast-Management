"""Web routes for dashboard and product detail pages."""

import json

from flask import Blueprint, abort, current_app, render_template

from inventory_app.data.loader import InventoryDataError, load_inventory_data
from inventory_app.data.preprocess import preprocess_data
from inventory_app.services.dashboard import (
    get_all_products_forecast,
    get_dashboard_metrics,
    get_forecast_for_product,
)

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def index():
    """Main dashboard page."""
    try:
        df = load_inventory_data(current_app.config["CSV_PATH"])
        df = preprocess_data(df)
    except InventoryDataError as exc:
        return render_template("dashboard.html", metrics=None, forecasts=[], load_error=str(exc))

    metrics = get_dashboard_metrics(
        df,
        periods=current_app.config["FORECAST_PERIODS"],
        store_id=current_app.config["DEFAULT_STORE_ID"],
    )
    forecasts = get_all_products_forecast(
        df,
        periods=current_app.config["FORECAST_PERIODS"],
        store_id=current_app.config["DEFAULT_STORE_ID"],
    )

    return render_template("dashboard.html", metrics=metrics, forecasts=forecasts, load_error=None)


@web_bp.route("/product/<product_id>")
def product_detail(product_id):
    """Product detail forecast page."""
    try:
        df = load_inventory_data(current_app.config["CSV_PATH"])
        df = preprocess_data(df)
    except InventoryDataError as exc:
        return render_template("product_detail.html", forecast=None, forecast_chart=None, load_error=str(exc))

    forecast = get_forecast_for_product(
        df,
        product_id,
        store_id=current_app.config["DEFAULT_STORE_ID"],
        periods=current_app.config["FORECAST_PERIODS"],
    )

    if not forecast:
        abort(
            404,
            description=(
                f"No forecast data found for product '{product_id}' in "
                f"store '{current_app.config['DEFAULT_STORE_ID']}'."
            ),
        )

    forecast_chart = json.dumps(
        {
            "data": [
                {
                    "x": forecast["historical_dates"],
                    "y": forecast["historical_values"],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Historical Units Sold",
                },
                {
                    "x": forecast["forecast_dates"],
                    "y": forecast["forecast_values"],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Forecast (yhat)",
                },
                {
                    "x": forecast["forecast_dates"] + forecast["forecast_dates"][::-1],
                    "y": forecast["forecast_upper"] + forecast["forecast_lower"][::-1],
                    "fill": "toself",
                    "fillcolor": "rgba(245, 158, 11, 0.20)",
                    "line": {"color": "rgba(245, 158, 11, 0)"},
                    "name": "Confidence Interval",
                    "type": "scatter",
                    "hoverinfo": "skip",
                },
            ],
            "layout": {
                "title": f"Demand Forecast for {forecast['product_id']}",
                "xaxis": {"title": "Date"},
                "yaxis": {"title": "Units Sold"},
            },
        }
    )

    return render_template(
        "product_detail.html",
        forecast=forecast,
        forecast_chart=forecast_chart,
        load_error=None,
    )
