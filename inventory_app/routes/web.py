"""Web routes for inventory views."""

import json

from flask import Blueprint, abort, render_template, request


def create_web_blueprint(load_data, preprocess_data, get_forecast_for_product, csv_path):
    """Create the web blueprint with dashboard and product detail routes."""
    web_bp = Blueprint("web", __name__)

    @web_bp.route("/product/<product_id>")
    def product_detail(product_id):
        store_id = request.args.get("store_id", "S001")

        df = preprocess_data(load_data(csv_path))
        forecast = get_forecast_for_product(df, product_id, store_id, 30)

        if forecast is None:
            abort(404, description=f"No forecast data found for product '{product_id}' in store '{store_id}'.")

        chart_payload = {
            "data": [
                {
                    "x": forecast["historical_dates"],
                    "y": forecast["historical_values"],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Historical Demand",
                    "line": {"color": "#667eea", "width": 2},
                },
                {
                    "x": forecast["forecast_dates"],
                    "y": forecast["forecast_values"],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Forecast Demand",
                    "line": {"color": "#f59e0b", "dash": "dash", "width": 2},
                },
                {
                    "x": forecast["forecast_dates"] + forecast["forecast_dates"][::-1],
                    "y": forecast["forecast_upper"] + forecast["forecast_lower"][::-1],
                    "fill": "toself",
                    "fillcolor": "rgba(245, 158, 11, 0.2)",
                    "line": {"color": "rgba(245, 158, 11, 0)"},
                    "name": "Confidence Interval",
                    "type": "scatter",
                    "hoverinfo": "skip",
                },
            ],
            "layout": {
                "title": f"Demand Trend and Forecast for {product_id}",
                "xaxis": {"title": "Date"},
                "yaxis": {"title": "Units Sold"},
                "legend": {"orientation": "h", "y": 1.1},
                "template": "plotly_white",
                "margin": {"l": 40, "r": 20, "t": 60, "b": 40},
            },
        }

        return render_template(
            "product_detail.html",
            forecast=forecast,
            forecast_chart=json.dumps(chart_payload),
        )

    return web_bp
