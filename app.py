"""
Inventory Forecasting POC for Grocery Delivery Company
=========================================================
This application predicts stockout dates for SKUs using time series forecasting.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Flask imports
from flask import Flask, render_template, jsonify, request

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

CSV_PATH = "C:/Users/arvinbrian.j/Desktop/DataSet/SYSCO_POC_DB/retail_store_inventory.csv"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'inventory-forecasting-poc-secret-key'

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
        raise ValueError("CSV path must be provided")
    
    try:
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        raise ValueError(f"Failed to load data from {csv_path}: {e}")


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
        return forecast_demand_simple(train_data, periods)
    
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
        
        return forecast
    except Exception as e:
        print(f"Prophet forecasting error: {e}")
        return forecast_demand_simple(train_data, periods)


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
    # Calculate moving average
    recent_demand = train_data['y'].tail(14).mean()
    
    # Calculate trend
    if len(train_data) >= 7:
        week_avg = train_data['y'].tail(7).mean()
        prev_week_avg = train_data['y'].tail(14).head(7).mean()
        trend = (week_avg - prev_week_avg) / 7
    else:
        trend = 0
    
    # Generate forecasts
    last_date = train_data['ds'].max()
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=periods)
    
    forecasts = []
    for i in range(periods):
        predicted = recent_demand + (trend * i)
        # Add some variability
        predicted = predicted * np.random.uniform(0.9, 1.1)
        forecasts.append(max(0, predicted))
    
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

def get_forecast_for_product(df, product_id, store_id='S001', periods=30):
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
    if PROPHET_AVAILABLE:
        forecast = forecast_demand_prophet(train_data, periods)
    else:
        forecast = forecast_demand_simple(train_data, periods)
    
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
    
    return {
        'product_id': product_id,
        'store_id': store_id,
        'current_inventory': current_inventory,
        'days_until_stockout': days_until_stockout,
        'stockout_date': stockout_date.strftime('%Y-%m-%d') if stockout_date else 'N/A',
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
        'historical_dates': train_data['ds'].dt.strftime('%Y-%m-%d').tolist(),
        'historical_values': train_data['y'].round(2).tolist()
    }


def get_all_products_forecast(df, periods=30):
    """
    Get forecast for all products.
    
    Args:
        df: Full inventory DataFrame
        periods: Number of days to forecast
    
    Returns:
        List of forecast dictionaries for all products
    """
    products = df['Product ID'].unique()
    forecasts = []
    
    for product_id in products:
        forecast = get_forecast_for_product(df, product_id, 'S001', periods)
        if forecast:
            forecasts.append(forecast)
    
    return forecasts


def get_dashboard_metrics(df):
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
    forecasts = get_all_products_forecast(df, 30)
    at_risk = sum(1 for f in forecasts if f['days_until_stockout'] < 7)
    low_stock = sum(1 for f in forecasts if 7 <= f['days_until_stockout'] < 14)
    healthy = sum(1 for f in forecasts if f['days_until_stockout'] >= 14)
    
    # Category breakdown
    category_inventory = latest_data.groupby('Category')['Inventory Level'].sum().to_dict()
    
    return {
        'total_inventory': int(total_inventory),
        'total_units_sold_30d': int(total_units_sold),
        'avg_daily_sales': round(avg_daily_sales, 2),
        'products_at_risk': at_risk,
        'products_low_stock': low_stock,
        'products_healthy': healthy,
        'total_products': len(forecasts),
        'category_inventory': category_inventory,
        'latest_date': latest_date.strftime('%Y-%m-%d')
    }


# ============================================
# FLASK ROUTES
# ============================================

@app.route('/')
def index():
    """
    Main dashboard page.
    """
    # Load data
    df = load_data(CSV_PATH)
    df = preprocess_data(df)
    
    # Get dashboard metrics
    metrics = get_dashboard_metrics(df)
    
    # Get all product forecasts
    forecasts = get_all_products_forecast(df, 30)
    
    return render_template(
        'dashboard.html',
        metrics=metrics,
        forecasts=forecasts
    )


@app.route('/api/metrics')
def api_metrics():
    """
    API endpoint for dashboard metrics.
    """
    df = load_data(CSV_PATH)
    df = preprocess_data(df)
    
    metrics = get_dashboard_metrics(df)
    
    return jsonify(metrics)


@app.route('/api/all-forecasts')
def api_all_forecasts():
    """
    API endpoint for all product forecasts.
    """
    df = load_data(CSV_PATH)
    df = preprocess_data(df)
    
    forecasts = get_all_products_forecast(df, 30)
    
    return jsonify(forecasts)


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
    
    app.run(debug=False, host='0.0.0.0', port=8000)
