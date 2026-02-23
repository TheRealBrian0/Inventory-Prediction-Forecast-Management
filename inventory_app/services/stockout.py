"""Stockout date calculations and recommendations."""

from datetime import datetime


def calculate_stockout_date(inventory_level, forecast_df):
    """Calculate estimated stockout date based on forecasted demand."""
    if inventory_level <= 0:
        return datetime.now(), 0

    forecast_df = forecast_df.copy()
    forecast_df['cumulative_demand'] = forecast_df['yhat'].cumsum()
    stockout_idx = forecast_df[forecast_df['cumulative_demand'] >= inventory_level].index

    if len(stockout_idx) > 0:
        first_idx = stockout_idx[0]
        stockout_date = forecast_df.loc[first_idx, 'ds']
        days_until_stockout = (stockout_date - datetime.now()).days
        return stockout_date, days_until_stockout

    return None, 999


def get_reorder_recommendation(days_until_stockout, lead_time=7):
    """Generate reorder recommendation based on stockout risk."""
    if days_until_stockout <= 0:
        return 'URGENT: Reorder immediately - stockout imminent!'
    if days_until_stockout <= lead_time:
        return (
            f'REORDER NOW: Stockout expected in {days_until_stockout} days '
            f'(lead time: {lead_time} days)'
        )
    if days_until_stockout <= lead_time * 2:
        return f'PREPARE TO ORDER: Consider reordering within {days_until_stockout - lead_time} days'
    return f'SUFFICIENT STOCK: No reorder needed for {days_until_stockout} days'
