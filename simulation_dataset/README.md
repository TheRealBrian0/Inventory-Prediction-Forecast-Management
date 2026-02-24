# Simulation Dataset Service

Independent data simulation service for `sysco_poc_db.retail_inventory`.

This service is separate from the Flask app and can be started/stopped on demand.

## What It Does
- Reads latest date from DB table.
- Generates **one new business day** of records per cycle.
- Inserts rows for **all products** across **all configured warehouses**.
- Runs every **3 real-world minutes** by default.
- Uses Ollama signals (if enabled) to vary demand/inventory regimes so SKUs land in mixed risk states.

## Warehouse Scope
Default simulated warehouse IDs:
- `S001,S002,S003,S004,S005`

Override using `SIM_WAREHOUSE_IDS` in env.

## Setup (venv)
Use your existing venv:

```powershell
.\.syscodb_env\Scripts\python -m pip install sqlalchemy pymysql python-dotenv
```

## Config
The simulator reads:
1. Root `.env` (DB credentials)
2. `simulation_dataset/.env` (optional overrides)

Optional simulator env file:

```powershell
Copy-Item simulation_dataset\.env.example simulation_dataset\.env
```

## Run One Cycle
Generates one new date then exits.

```powershell
.\.syscodb_env\Scripts\python .\simulation_dataset\simulator.py --once
```

## Run Continuously (Start/Stop)
Start background loop (default 180s):

```powershell
.\simulation_dataset\start_simulator.ps1
```

Stop:

```powershell
.\simulation_dataset\stop_simulator.ps1
```

Status:

```powershell
.\simulation_dataset\status_simulator.ps1
```

Logs:
- `simulation_dataset/simulator.log`
- PID file: `simulation_dataset/simulator.pid`
