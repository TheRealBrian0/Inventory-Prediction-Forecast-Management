"""
Inventory Forecasting POC for Grocery Delivery Company
This application predicts stockout dates for SKUs using time series forecasting.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import warnings
warnings.filterwarnings('ignore')
"""Backward-compatible app module that exposes Flask app."""

from inventory_app import create_app

# Flask imports
from flask import Flask, render_template, jsonify
from inventory_app.routes.web import create_web_blueprint
app = create_app()


if __name__ == '__main__':
from inventory_app.config import CsvPathResolutionError, resolve_csv_path
from inventory_app.data.loader import (
    InventoryDataError,
    InventoryDataFileMissingError,
    load_inventory_data,
)

# Forecasting imports - trying Prophet first, then fbprophet fallback
PROPHET_AVAILABLE = False
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
    print("Using Prophet for time series forecasting")
except ImportError:
    try:
        from fbprophet import Prophet
        PROPHET_AVAILABLE = True
        print("Using fbprophet for time series forecasting")
    except ImportError:
        print("Warning: Prophet not available")

# ============================================
# CONFIGURATION
# ============================================

CSV_PATH = None


def get_csv_path():
    """Resolve configured CSV path when needed."""
    return resolve_csv_path()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'inventory-forecasting-poc-secret-key'
logger = logging.getLogger(__name__)

DEFAULT_STOCKOUT_HORIZON_DAYS = 14

# ============================================
# DATA LOADING AND PROCESSING
# ============================================

def load_data(csv_path=None):
    """
    Load inventory data from CSV file.
    
    Args:
        csv_path: Path to the CSV file.
    
    Returns:
        DataFrame with inventory data
    """
    if csv_path is None:
        raise InventoryDataFileMissingError("CSV path must be provided")

    return load_inventory_data(csv_path)


def preprocess_data(df):
    """
    Preprocess the inventory data for forecasting.
    """
    # Convert date column
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Sort by date and product
    df = df.sort_values(['Product ID', 'Date'])
    
    return df


def get_product_summary(df):
    """
    Get current inventory summary per product.
    """
    latest_date = df['Date'].max()
    latest_data = df[df['Date'] == latest_date].copy()
    
    summary = latest_data.groupby('Product ID').agg({
        'Inventory Level': 'last',
        'Units Sold': 'sum',
        'Demand Forecast': 'mean',
        'Price': 'mean',
        'Category': 'first'
    }).reset_index()
    
    return summary


# ============================================
# FORECASTING MODULE
# ============================================

def forecast_demand_prophet(train_data, periods=30):
    """
    Forecast demand using Prophet.
    
    Args:
        train_data: DataFrame with 'ds' (date) and 'y' (demand) columns
        periods: Number of days to forecast
    
    Returns:
        DataFrame with forecasted values
    """
    if not PROPHET_AVAILABLE:
        fallback_forecast = forecast_demand_simple(train_data, periods)
        return fallback_forecast, 'fallback', 'Prophet library unavailable'
    
    try:
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05
        )
        model.fit(train_data)
        
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        
        return forecast, 'prophet', None
    except Exception as e:
        logger.exception("Prophet forecasting error")
        fallback_forecast = forecast_demand_simple(train_data, periods)
        return fallback_forecast, 'fallback', str(e)


def forecast_demand_simple(train_data, periods=30):
    """
    Simple forecasting method using moving average and trend.
    Used as fallback when Prophet/ARIMA not available.
    
    Args:
        train_data: DataFrame with 'ds' (date) and 'y' (demand) columns
        periods: Number of days to forecast
    
    Returns:
        DataFrame with forecasted values
    """
    history = train_data['y'].astype(float).reset_index(drop=True)
    lookback = min(len(history), 14)

    # Deterministic rolling-mean baseline
    recent_demand = history.tail(lookback).mean() if lookback > 0 else 0.0

    # Deterministic linear trend (daily slope)
    if len(history) >= 2:
        x = np.arange(len(history))
        trend = np.polyfit(x, history.values, 1)[0]
    else:
        trend = 0.0
    
    # Generate forecasts
    last_date = train_data['ds'].max()
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=periods)
    
    forecasts = []
    for i in range(periods):
        predicted = recent_demand + (trend * i)
        forecasts.append(max(0.0, predicted))
    
    forecast_df = pd.DataFrame({
        'ds': future_dates,
        'yhat': forecasts,
        'yhat_lower': [f * 0.85 for f in forecasts],
        'yhat_upper': [f * 1.15 for f in forecasts]
    })
    
    return forecast_df


def calculate_stockout_date(inventory_level, forecast_df):
    """
    Calculate estimated stockout date based on current inventory and forecasted demand.
    
    Args:
        inventory_level: Current inventory level
        forecast_df: DataFrame with forecasted daily demand
    
    Returns:
        Tuple of (stockout_date, days_until_stockout)
    """
    if inventory_level <= 0:
        return datetime.now(), 0
    
    # Calculate cumulative demand
    forecast_df = forecast_df.copy()
    forecast_df['cumulative_demand'] = forecast_df['yhat'].cumsum()
    
    # Find first day where cumulative demand exceeds inventory
    stockout_idx = forecast_df[forecast_df['cumulative_demand'] >= inventory_level].index
    
    if len(stockout_idx) > 0:
        first_idx = stockout_idx[0]
        stockout_date = forecast_df.loc[first_idx, 'ds']
        days_until_stockout = (stockout_date - datetime.now()).days
        return stockout_date, days_until_stockout
    else:
        # Not expected to stockout within forecast period
        return None, 999


def get_reorder_recommendation(days_until_stockout, lead_time=7):
    """
    Generate reorder recommendation based on days until stockout.
    
    Args:
        days_until_stockout: Days until inventory reaches zero
        lead_time: Supplier lead time in days (default 7)
    
    Returns:
        Recommendation string
    """
    if days_until_stockout <= 0:
        return "URGENT: Reorder immediately - stockout imminent!"
    elif days_until_stockout <= lead_time:
        return f"REORDER NOW: Stockout expected in {days_until_stockout} days (lead time: {lead_time} days)"
    elif days_until_stockout <= lead_time * 2:
        return f"PREPARE TO ORDER: Consider reordering within {days_until_stockout - lead_time} days"
    else:
        return f"SUFFICIENT STOCK: No reorder needed for {days_until_stockout} days"


# ============================================
# ANALYTICS FUNCTIONS
# ============================================

def get_forecast_for_product(df, product_id, store_id='S001', periods=DEFAULT_STOCKOUT_HORIZON_DAYS):
    """
    Get forecast for a specific product.
    
    Args:
        df: Full inventory DataFrame
        product_id: Product ID to forecast
        store_id: Store ID (default S001)
        periods: Number of days to forecast
    
    Returns:
        Dictionary with forecast data and stockout analysis
    """
    # Filter data for this product
    product_data = df[(df['Product ID'] == product_id) & (df['Store ID'] == store_id)].copy()
    
    if len(product_data) == 0:
        return None
    
    # Prepare data for Prophet
    train_data = pd.DataFrame({
        'ds': product_data['Date'],
        'y': product_data['Units Sold']
    })
    
    # Get forecast
    fallback_reason = None
    if PROPHET_AVAILABLE:
        forecast, model_used, fallback_reason = forecast_demand_prophet(train_data, periods)
    else:
        forecast = forecast_demand_simple(train_data, periods)
        model_used = 'fallback'
        fallback_reason = 'Prophet library unavailable'

    if fallback_reason:
        logger.warning(
            "Using fallback forecast for SKU %s (store %s): %s",
            product_id,
            store_id,
            fallback_reason
        )
    
    # Get current inventory
    current_inventory = product_data['Inventory Level'].iloc[-1]
    
    # Calculate stockout date
    stockout_date, days_until_stockout = calculate_stockout_date(current_inventory, forecast)
    
    # Get recommendation
    recommendation = get_reorder_recommendation(days_until_stockout)
    
    # Calculate key metrics
    avg_daily_demand = product_data['Units Sold'].mean()
    max_daily_demand = product_data['Units Sold'].max()
    min_daily_demand = product_data['Units Sold'].min()
    
    # Forecast summary
    total_forecasted_demand = forecast['yhat'].sum()
    avg_forecasted_demand = forecast['yhat'].mean()
    cumulative_forecast = forecast['yhat'].cumsum()
    cumulative_horizon_demand = cumulative_forecast.iloc[-1] if len(cumulative_forecast) > 0 else 0
    stockout_within_horizon = days_until_stockout <= periods
    stockout_date_within_horizon = stockout_date.strftime('%Y-%m-%d') if stockout_within_horizon and stockout_date else None
    
    return {
        'product_id': product_id,
        'store_id': store_id,
        'current_inventory': current_inventory,
        'days_until_stockout': days_until_stockout,
        'stockout_date': stockout_date.strftime('%Y-%m-%d') if stockout_date else 'N/A',
        'forecast_horizon_days': periods,
        'horizon_demand_forecast': round(total_forecasted_demand, 2),
        'cumulative_horizon_demand': round(cumulative_horizon_demand, 2),
        'stockout_within_horizon': stockout_within_horizon,
        'stockout_date_within_horizon': stockout_date_within_horizon,
        'recommendation': recommendation,
        'avg_daily_demand': round(avg_daily_demand, 2),
        'max_daily_demand': round(max_daily_demand, 2),
        'min_daily_demand': round(min_daily_demand, 2),
        'total_forecasted_demand': round(total_forecasted_demand, 2),
        'avg_forecasted_demand': round(avg_forecasted_demand, 2),
        'forecast_dates': forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
        'forecast_values': forecast['yhat'].round(2).tolist(),
        'forecast_lower': forecast['yhat_lower'].round(2).tolist(),
        'forecast_upper': forecast['yhat_upper'].round(2).tolist(),
        'model_used': model_used,
        'fallback_reason': fallback_reason,
        'historical_dates': train_data['ds'].dt.strftime('%Y-%m-%d').tolist(),
        'historical_values': train_data['y'].round(2).tolist()
    }


def get_all_products_forecast(df, periods=DEFAULT_STOCKOUT_HORIZON_DAYS):
    """
    Get forecast for all products.
    
    Args:
        df: Full inventory DataFrame
        periods: Number of days to forecast
    
    Returns:
        List of forecast dictionaries for all products
    """
    store_products = (
        df[['Store ID', 'Product ID']]
        .drop_duplicates()
        .sort_values(['Store ID', 'Product ID'])
        .itertuples(index=False)
    )
    forecasts = []
    
    for store_id, product_id in store_products:
        forecast = get_forecast_for_product(df, product_id, store_id, periods)
        if forecast:
            forecasts.append(forecast)
    
    return forecasts


def get_dashboard_metrics(df, stockout_horizon_days=DEFAULT_STOCKOUT_HORIZON_DAYS):
    """
    Get key dashboard metrics.
    
    Args:
        df: Full inventory DataFrame
    
    Returns:
        Dictionary with dashboard metrics
    """
    # Get latest data
    latest_date = df['Date'].max()
    latest_data = df[df['Date'] == latest_date]
    
    # Total inventory value
    total_inventory = latest_data['Inventory Level'].sum()
    
    # Total units sold (last 30 days)
    last_30_days = df[df['Date'] >= latest_date - timedelta(days=30)]
    total_units_sold = last_30_days['Units Sold'].sum()
    
    # Average daily sales
    avg_daily_sales = df.groupby('Date')['Units Sold'].sum().mean()
    
    # Products at risk (less than 7 days of stock)
    forecasts = get_all_products_forecast(df, stockout_horizon_days)
    stockout_le_3_days = sum(1 for f in forecasts if f['days_until_stockout'] <= 3)
    stockout_4_7_days = sum(1 for f in forecasts if 4 <= f['days_until_stockout'] <= 7)
    stockout_8_14_days = sum(1 for f in forecasts if 8 <= f['days_until_stockout'] <= stockout_horizon_days)
    stockout_gt_14_days = sum(1 for f in forecasts if f['days_until_stockout'] > stockout_horizon_days)
    
    # Category breakdown
    category_inventory = latest_data.groupby('Category')['Inventory Level'].sum().to_dict()
    
    return {
        'total_inventory': int(total_inventory),
        'total_units_sold_30d': int(total_units_sold),
        'avg_daily_sales': round(avg_daily_sales, 2),
        'stockout_horizon_days': stockout_horizon_days,
        'stockout_le_3_days': stockout_le_3_days,
        'stockout_4_7_days': stockout_4_7_days,
        'stockout_8_14_days': stockout_8_14_days,
        'stockout_gt_14_days': stockout_gt_14_days,
        'total_products': len(forecasts),
        'category_inventory': category_inventory,
        'latest_date': latest_date.strftime('%Y-%m-%d')
    }


# ============================================
# FLASK ROUTES
# ============================================

# Register additional web routes
app.register_blueprint(
    create_web_blueprint(load_data, preprocess_data, get_forecast_for_product, CSV_PATH)
)


@app.route('/')
def index():
    """
    Main dashboard page.
    """
    # Load data
    df = load_data(CSV_PATH)
    df = preprocess_data(df)
    
    # Get dashboard metrics
    stockout_horizon_days = request.args.get('horizon_days', default=DEFAULT_STOCKOUT_HORIZON_DAYS, type=int)
    metrics = get_dashboard_metrics(df, stockout_horizon_days)
    
    # Get all product forecasts
    forecasts = get_all_products_forecast(df, stockout_horizon_days)
    
    return render_template(
        'dashboard.html',
        metrics=metrics,
        forecasts=forecasts
    )
    try:
        # Load data
        df = load_data(get_csv_path())
        df = preprocess_data(df)

        # Get dashboard metrics
        metrics = get_dashboard_metrics(df)

        # Get all product forecasts
        forecasts = get_all_products_forecast(df, 30)

        return render_template(
            'dashboard.html',
            metrics=metrics,
            forecasts=forecasts,
            load_error=None
        )
    except (CsvPathResolutionError, InventoryDataError) as exc:
        return render_template(
            'dashboard.html',
            metrics=None,
            forecasts=[],
            load_error=str(exc)
        )


@app.route('/api/metrics')
def api_metrics():
    """
    API endpoint for dashboard metrics.
    """
    df = load_data(CSV_PATH)
    df = preprocess_data(df)
    
    stockout_horizon_days = request.args.get('horizon_days', default=DEFAULT_STOCKOUT_HORIZON_DAYS, type=int)
    metrics = get_dashboard_metrics(df, stockout_horizon_days)
    
    return jsonify(metrics)
    try:
        df = load_data(get_csv_path())
        df = preprocess_data(df)

        metrics = get_dashboard_metrics(df)

        return jsonify(metrics)
    except (CsvPathResolutionError, InventoryDataError) as exc:
        return jsonify({"error": str(exc)}), 503


@app.route('/api/all-forecasts')
def api_all_forecasts():
    """
    API endpoint for all product forecasts.
    """
    df = load_data(CSV_PATH)
    df = preprocess_data(df)
    
    stockout_horizon_days = request.args.get('horizon_days', default=DEFAULT_STOCKOUT_HORIZON_DAYS, type=int)
    forecasts = get_all_products_forecast(df, stockout_horizon_days)
    
    return jsonify(forecasts)
    try:
        df = load_data(get_csv_path())
        df = preprocess_data(df)

        forecasts = get_all_products_forecast(df, 30)

        return jsonify(forecasts)
    except (CsvPathResolutionError, InventoryDataError) as exc:
        return jsonify({"error": str(exc)}), 503


@app.route('/health')
def health():
    """Health endpoint that does not depend on CSV readiness."""
    return jsonify({"status": "ok"}), 200


@app.errorhandler(404)
def not_found(error):
    """Readable 404 response for missing product/store combinations."""
    return f"<h2>Not Found</h2><p>{error.description if hasattr(error, 'description') else 'The requested resource was not found.'}</p>", 404


# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("Inventory Forecasting POC - Starting Server")
    print("=" * 60)
    print("\nAvailable Features:")
    print("- Dashboard: http://localhost:8000/")
    print("- Product Detail: http://localhost:8000/product/<product_id>")
    print("- API Metrics: http://localhost:8000/api/metrics")
    print("- API Forecasts: http://localhost:8000/api/all-forecasts")
    print("\nForecasting Method: " + ("Prophet" if PROPHET_AVAILABLE else "Simple Moving Average"))
    print("=" * 60)

    try:
        print(f"Using inventory CSV: {get_csv_path()}")
    except CsvPathResolutionError as exc:
        raise SystemExit(f"Startup configuration error: {exc}") from exc

    app.run(debug=False, host='0.0.0.0', port=8000)
