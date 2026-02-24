# Inventory Prediction Forecast Management

Flask web app for inventory risk monitoring and stockout forecasting by SKU/store.

## What It Does
- Loads historical inventory/sales data from a CSV file.
- Forecasts short-term demand per product (Prophet when available, fallback model otherwise).
- Estimates days until stockout from current inventory vs forecasted demand.
- Shows:
1. Dashboard with product risk buckets.
2. Product detail page with forecast chart and recommendation.
3. JSON APIs for metrics and all forecasts.

## Project Flow (Brief)
1. `app.py` creates the Flask app using `inventory_app.create_app()`.
2. Routes load + validate CSV via `inventory_app/data/loader.py`.
3. Data is preprocessed (`Date` parsing/sorting) in `inventory_app/data/preprocess.py`.
4. Forecasting runs from `inventory_app/forecasting/*`.
5. Stockout/reorder logic is computed in `inventory_app/services/*`.
6. Results are rendered in `templates/` or returned from `/api/*`.

## Requirements
- Python 3.10+ recommended
- Install dependencies:

```bash
pip install -r requirements.txt
```

## CSV Input Requirements
The CSV must contain these columns:
- `Date`
- `Store ID`
- `Product ID`
- `Inventory Level`
- `Units Sold`
- `Demand Forecast`
- `Price`
- `Category`

## Configuration
Use environment variables (from shell or `.env`):
- `DATA_SOURCE`: `csv` or `mysql`
- `INVENTORY_CSV_PATH` (preferred): full path to your CSV file
- `CSV_PATH` (legacy fallback): full path to your CSV file
- `FORECAST_PERIODS` (default: `30`)
- `DEFAULT_STORE_ID` (default: `S001`)
- `SECRET_KEY` (optional Flask secret)
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_TABLE` (for MySQL mode)

### `.env` (recommended)

Create a `.env` in the project root:

```env
DATA_SOURCE=mysql
INVENTORY_CSV_PATH=C:\Users\arvinbrian.j\Desktop\DataSet\SYSCO_POC_DB\retail_store_inventory.csv
FORECAST_PERIODS=30
DEFAULT_STORE_ID=S001
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=sysco_poc_db
DB_TABLE=retail_inventory
```

The app auto-loads `.env` on startup.

### PowerShell example

```powershell
$env:INVENTORY_CSV_PATH="C:\path\to\retail_store_inventory.csv"
$env:FORECAST_PERIODS="30"
$env:DEFAULT_STORE_ID="S001"
```

## Run

```bash
python app.py
```

Server defaults:
- Host: `0.0.0.0`
- Port: `8000`

## Routes
- Dashboard: `http://localhost:8000/`
- Product detail: `http://localhost:8000/product/<product_id>`
- API metrics: `http://localhost:8000/api/metrics`
- API all forecasts: `http://localhost:8000/api/all-forecasts`

## Notes
- If Prophet is installed (`prophet` or `fbprophet`), it is used automatically.
- If CSV is missing/invalid, web pages show a readable error and APIs return `503` with an error message.

## Independent Data Simulator
- Path: `simulation_dataset/`
- Purpose: generate one new logical day of rows every 3 minutes for all products and warehouses (`S001`-`S005`).
- Start: `.\simulation_dataset\start_simulator.ps1`
- Stop: `.\simulation_dataset\stop_simulator.ps1`
- One cycle only: `.\.syscodb_env\Scripts\python .\simulation_dataset\simulator.py --once`
- Details: `simulation_dataset/README.md`

## Reorder Calculation Logic
1. For each SKU, the model forecasts daily demand for the next `FORECAST_PERIODS` days.
2. Forecast demand is cumulatively summed day by day.
3. The first day where cumulative demand is greater than or equal to current inventory is treated as stockout date.
4. `days_until_stockout` is computed as:
   - `stockout_date - latest_data_date` (not system clock date).
5. If no stockout is found inside the forecast horizon:
   - `stockout_date = N/A`
   - recommendation = `SUFFICIENT STOCK: No stockout expected within the next <horizon> days.`
   - UI shows days as `>horizon` (for example `>30`).

## Status Buckets
- `At Risk`: stockout in `< 7` days
- `Low Stock`: stockout in `7-13` days
- `Healthy`: stockout in `>= 14` days or not within forecast horizon

## End-to-End Workflow
### Main App
1. Load inventory data (CSV or MySQL based on `DATA_SOURCE`).
2. Preprocess dates and sort by SKU/date.
3. Forecast demand per SKU (`Prophet` when available, fallback model otherwise).
4. Compute stockout date, days-to-stockout, and reorder recommendation.
5. Render dashboard/product pages and expose API endpoints.

### Simulator Service (`simulation_dataset/`)
1. Reads latest date from `retail_inventory`.
2. Creates next logical date (`latest + 1 day`).
3. Generates rows for all products across warehouses (`S001`-`S005`) with controlled variability.
4. Inserts generated rows into MySQL.
5. Repeats every 180 seconds when run in loop mode.
