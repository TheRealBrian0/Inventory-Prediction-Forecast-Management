"""Dashboard service logic and forecast orchestration."""

from datetime import timedelta
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

import pandas as pd

try:
    from sqlalchemy import create_engine, text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

from inventory_app.forecasting.fallback import forecast_demand_simple
from inventory_app.forecasting.prophet_service import PROPHET_AVAILABLE, forecast_demand_prophet
from inventory_app.services.stockout import calculate_stockout_date, get_reorder_recommendation

WAREHOUSE_REGION_MAP = {
    "S001": "North",
    "S002": "South",
    "S003": "East",
    "S004": "West",
    "S005": "Central",
}

# Cache for forecasts: key is (store_id, periods), value is list of forecasts
forecast_cache = {}


def get_forecast_for_product(df, product_id, store_id='S001', periods=30):
    """Get forecast and stockout analysis for a specific product."""
    product_data = df[(df['Product ID'] == product_id) & (df['Store ID'] == store_id)].copy()

    if len(product_data) == 0:
        return None

    train_data = pd.DataFrame({'ds': product_data['Date'], 'y': product_data['Units Sold']})

    if PROPHET_AVAILABLE:
        forecast = forecast_demand_prophet(train_data, periods)
    else:
        forecast = forecast_demand_simple(train_data, periods)

    # Prophet returns historical + future rows; keep only future horizon rows.
    last_history_date = train_data['ds'].max()
    forecast = forecast[forecast['ds'] > last_history_date].copy()
    forecast = forecast.sort_values('ds').head(periods)

    if forecast.empty:
        return None

    # Keep demand predictions non-negative and interval ordering sane for display.
    forecast['yhat'] = forecast['yhat'].clip(lower=0)
    forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)
    forecast['yhat_upper'] = forecast['yhat_upper'].clip(lower=0)
    forecast['yhat_lower'] = forecast[['yhat_lower', 'yhat']].min(axis=1)
    forecast['yhat_upper'] = forecast[['yhat_upper', 'yhat']].max(axis=1)

    current_inventory = float(product_data['Inventory Level'].iloc[-1])
    stockout_date, days_until_stockout = calculate_stockout_date(
        current_inventory,
        forecast,
        reference_date=product_data['Date'].max(),
    )
    stockout_within_horizon = days_until_stockout is not None
    days_until_stockout_for_scoring = days_until_stockout if stockout_within_horizon else periods + 1
    recommendation = get_reorder_recommendation(
        days_until_stockout,
        horizon_days=periods,
    )

    avg_daily_demand = product_data['Units Sold'].mean()
    max_daily_demand = product_data['Units Sold'].max()
    min_daily_demand = product_data['Units Sold'].min()

    total_forecasted_demand = forecast['yhat'].sum()
    avg_forecasted_demand = forecast['yhat'].mean()

    return {
        'product_id': product_id,
        'store_id': store_id,
        'current_inventory': int(round(current_inventory)),
        'days_until_stockout': int(days_until_stockout_for_scoring),
        'days_until_stockout_display': (
            str(int(days_until_stockout)) if stockout_within_horizon else f">{periods}"
        ),
        'stockout_within_horizon': stockout_within_horizon,
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
        'historical_values': train_data['y'].round(2).tolist(),
        'available_stores_categorized': get_available_stores(df, product_id, store_id),
    }


def get_all_products_forecast(df, periods=30, store_id='S001'):
    """Get forecasts for all products in the dataframe."""
    cache_key = (store_id, periods, df['Date'].max())
    if cache_key in forecast_cache:
        return forecast_cache[cache_key]

    products = sorted(
        df[df['Store ID'] == store_id]['Product ID'].dropna().unique()
    )
    forecasts = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_product = {executor.submit(get_forecast_for_product, df, product_id, store_id, periods): product_id for product_id in products}
        for future in as_completed(future_to_product):
            forecast = future.result()
            if forecast:
                forecasts.append(forecast)

    forecast_cache[cache_key] = forecasts
    return forecasts


def get_available_stores(df, product_id, current_store_id):
    """Get categorized stores for the product, only including sufficient stock warehouses."""
    all_stores = df['Store ID'].unique()

    sufficient_stores = []
    no_stock_stores = []

    for store_id in all_stores:
        store_product_data = df[(df['Product ID'] == product_id) & (df['Store ID'] == store_id)].copy()
        if store_product_data.empty:
            no_stock_stores.append(store_id)
            continue

        current_inventory = store_product_data['Inventory Level'].iloc[-1]
        if current_inventory <= 0:
            no_stock_stores.append(store_id)
            continue

        # Compute days_until_stockout using the same forecast method as main logic
        train_data = pd.DataFrame({'ds': store_product_data['Date'], 'y': store_product_data['Units Sold']})
        if PROPHET_AVAILABLE:
            forecast = forecast_demand_prophet(train_data, periods=30)
        else:
            forecast = forecast_demand_simple(train_data, periods=30)
        last_history_date = train_data['ds'].max()
        forecast = forecast[forecast['ds'] > last_history_date].copy()
        forecast = forecast.sort_values('ds').head(30)

        if forecast.empty:
            no_stock_stores.append(store_id)
            continue

        stockout_date, days_until_stockout = calculate_stockout_date(
            current_inventory, forecast, reference_date=store_product_data['Date'].max()
        )
        days_until_stockout_for_scoring = days_until_stockout if days_until_stockout is not None else 31

        if days_until_stockout_for_scoring >= 14:
            sufficient_stores.append(store_id)
        else:
            no_stock_stores.append(store_id)

    current_region = WAREHOUSE_REGION_MAP.get(current_store_id, "")
    same_region_sufficient = [s for s in sufficient_stores if WAREHOUSE_REGION_MAP.get(s, "") == current_region and s != current_store_id]
    other_sufficient = [s for s in sufficient_stores if s not in same_region_sufficient and s != current_store_id]
    same_region_no_stock = [s for s in no_stock_stores if WAREHOUSE_REGION_MAP.get(s, "") == current_region and s != current_store_id]
    other_no_stock = [s for s in no_stock_stores if s not in same_region_no_stock and s != current_store_id]

    return {
        'same_region': same_region_sufficient,
        'other': other_sufficient,
        'no_stock': same_region_no_stock + other_no_stock
    }


def get_dashboard_metrics(df, periods=30, store_id='S001'):
    """Get key dashboard metrics for current data and forecast horizon."""
    latest_date = df['Date'].max()
    latest_data = df[df['Date'] == latest_date]

    total_inventory = latest_data['Inventory Level'].sum()

    last_30_days = df[df['Date'] >= latest_date - timedelta(days=30)]
    total_units_sold = last_30_days['Units Sold'].sum()

    avg_daily_sales = df.groupby('Date')['Units Sold'].sum().mean()

    forecasts = get_all_products_forecast(df, periods, store_id)
    at_risk = sum(1 for f in forecasts if f['days_until_stockout'] < 7)
    low_stock = sum(1 for f in forecasts if 7 <= f['days_until_stockout'] < 14)
    healthy = sum(1 for f in forecasts if f['days_until_stockout'] >= 14)

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
        'latest_date': latest_date.strftime('%Y-%m-%d'),
    }
