"""Entrypoint for running the Inventory Forecasting application."""

from inventory_app import create_app
from inventory_app.forecasting.prophet_service import PROPHET_AVAILABLE

app = create_app()


if __name__ == '__main__':
    print('=' * 60)
    print('Inventory Forecasting POC - Starting Server')
    print('=' * 60)
    print('\nAvailable Features:')
    print('- Dashboard: http://localhost:8000/')
    print('- Product Detail: http://localhost:8000/product/<product_id>')
    print('- API Metrics: http://localhost:8000/api/metrics')
    print('- API Forecasts: http://localhost:8000/api/all-forecasts')
    print('\nForecasting Method: ' + ('Prophet' if PROPHET_AVAILABLE else 'Simple Moving Average'))
    print('=' * 60)

    app.run(debug=False, host='0.0.0.0', port=8000)
