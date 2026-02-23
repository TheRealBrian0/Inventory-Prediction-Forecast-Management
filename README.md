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
1. `run.py` creates the Flask app using `inventory_app.create_app()`.
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
- `INVENTORY_CSV_PATH` (preferred): full path to your CSV file
- `CSV_PATH` (legacy fallback): full path to your CSV file
- `FORECAST_PERIODS` (default: `30`)
- `DEFAULT_STORE_ID` (default: `S001`)
- `SECRET_KEY` (optional Flask secret)

### `.env` (recommended)

Create a `.env` in the project root:

```env
INVENTORY_CSV_PATH=C:\Users\arvinbrian.j\Desktop\DataSet\SYSCO_POC_DB\retail_store_inventory.csv
FORECAST_PERIODS=30
DEFAULT_STORE_ID=S001
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
python run.py
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
