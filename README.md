# Inventory Prediction Forecast Management

FastAPI-based inventory risk monitoring and stockout forecasting by SKU/store.

## What It Does
- Loads historical inventory/sales data from CSV or MySQL.
- Forecasts short-term demand per product (Prophet when available, fallback otherwise).
- Estimates days until stockout from current inventory vs forecasted demand.
- Serves:
1. React-based dashboard and product pages (client-side frontend).
2. JSON API endpoints for data consumption.

## Current Architecture (FastAPI + React)
- `app.py`: ASGI entrypoint and local `uvicorn` startup.
- `inventory_app/__init__.py`: app factory, CORS setup, router registration, static file serving for React.
- `inventory_app/core/settings.py`: centralized environment-driven settings.
- `inventory_app/dependencies/data.py`: shared data loading + preprocessing dependency.
- `inventory_app/routes/api.py`: versioned JSON APIs (`/api/v1/*`) plus legacy aliases.
- `inventory_app/schemas/api.py`: typed response contracts for API consumers.
- `frontend/`: React application with components for dashboard and product details.
- Business logic remains in:
  - `inventory_app/data/*`
  - `inventory_app/forecasting/*`
  - `inventory_app/services/*`

## Why This Is React-Ready
- Versioned API namespace: `/api/v1`.
- Stable typed response models (Pydantic) for forecasts/metrics.
- CORS support via `CORS_ORIGINS` env variable.
- Store and horizon overrides exposed as query params for client-driven filtering.

## Requirements
- Python 3.10+ recommended
- Node.js 16+ for React frontend

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install React dependencies:

```bash
cd frontend
npm install
```

## CSV Input Requirements
The source dataset must expose these business columns (CSV names or MySQL mapped names):
- `Date`
- `Store ID`
- `Product ID`
- `Inventory Level`
- `Units Sold`
- `Demand Forecast`
- `Price`
- `Category`

## Configuration
Use environment variables (shell or `.env`):
- `DATA_SOURCE`: `csv` or `mysql`
- `INVENTORY_CSV_PATH` (preferred) or `CSV_PATH`
- `FORECAST_PERIODS` (default: `30`)
- `DEFAULT_STORE_ID` (default: `S001`)
- `CORS_ORIGINS` (default: `*`, comma-separated for multi-origin)
- `HOST` (default: `0.0.0.0`)
- `PORT` (default: `8000`)
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_TABLE` (MySQL mode)

Example `.env`:

```env
DATA_SOURCE=mysql
INVENTORY_CSV_PATH=C:\Users\arvinbrian.j\Desktop\DataSet\SYSCO_POC_DB\retail_store_inventory.csv
FORECAST_PERIODS=30
DEFAULT_STORE_ID=S001
CORS_ORIGINS=*
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=sysco_poc_db
DB_TABLE=retail_inventory
```

## Run

Start the backend:

```bash
python app.py
```

In a separate terminal, start the React frontend:

```bash
cd frontend
npm start
```

Server defaults:
- Host: `0.0.0.0`
- Port: `8000` (backend), `3000` (frontend dev server)

For production, build the React app:

```bash
cd frontend
npm run build
```

Then the backend will serve the built React app.

## Routes
### React Frontend
- Dashboard: `http://localhost:8000/`
- Product detail: `http://localhost:8000/product/<product_id>`

### API (React-ready)
- OpenAPI docs: `http://localhost:8000/api/docs`
- Health: `http://localhost:8000/api/v1/health`
- Metrics: `http://localhost:8000/api/v1/metrics`
- All forecasts: `http://localhost:8000/api/v1/forecasts`
- Product forecast: `http://localhost:8000/api/v1/forecasts/<product_id>`

### Legacy API aliases (kept for compatibility)
- `http://localhost:8000/api/metrics`
- `http://localhost:8000/api/all-forecasts`

## Independent Data Simulator
- Path: `simulation_dataset/`
- Purpose: generate one new logical day of rows every 3 minutes for all products and warehouses (`S001`-`S005`).
- Start: `./simulation_dataset/start_simulator.ps1`
- Stop: `./simulation_dataset/stop_simulator.ps1`
- One cycle only: `./.syscodb_env/Scripts/python ./simulation_dataset/simulator.py --once`
- Details: `simulation_dataset/README.md`

## Reorder Calculation Logic
1. Forecast daily demand for next `FORECAST_PERIODS` days.
2. Cumulatively sum forecast demand.
3. First day cumulative demand reaches inventory is stockout date.
4. `days_until_stockout = stockout_date - latest_data_date`.
5. If none within horizon:
   - `stockout_date = N/A`
   - recommendation = `SUFFICIENT STOCK: No stockout expected within the next <horizon> days.`
   - UI days display = `>horizon`

## Status Buckets
- `At Risk`: stockout in `< 7` days
- `Low Stock`: stockout in `7-13` days
- `Healthy`: stockout in `>= 14` days or outside forecast horizon

