"""Preprocessing functions for inventory data."""

import pandas as pd


def preprocess_data(df):
    """Preprocess the inventory data for forecasting."""
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(['Product ID', 'Date'])
    return df


def get_product_summary(df):
    """Get current inventory summary per product."""
    latest_date = df['Date'].max() #to find most recent date in df
    latest_data = df[df['Date'] == latest_date].copy() #to get all rows from that latest existing date

    summary = latest_data.groupby('Product ID').agg({
        'Inventory Level': 'last',
        'Units Sold': 'sum',
        'Demand Forecast': 'mean',
        'Price': 'mean',
        'Category': 'first',
    }).reset_index()

    return summary
