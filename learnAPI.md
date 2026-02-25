# Learn FastAPI and This Project Migration

## Purpose of this document
This guide explains:
1. What FastAPI is and why teams use it.
2. What changed in your project when we moved from Flask to FastAPI.
3. How to explain these changes clearly to a manager.
4. How this design keeps your current Python-rendered UI while making React adoption easy later.

---

## 1) FastAPI in simple terms

FastAPI is a modern Python web framework for building APIs quickly and safely.

### Why FastAPI is popular
- **Automatic API docs**: Swagger UI generated from code (`/api/docs`).
- **Type hints + validation**: request/response data is validated automatically.
- **High performance**: built on ASGI stack (Starlette + Pydantic).
- **Developer productivity**: less boilerplate for APIs than many older frameworks.

### Core FastAPI concepts you now use
- **App instance**: main application object (`FastAPI(...)`).
- **Routers**: split endpoints by domain (`web` routes vs `api` routes).
- **Pydantic models**: define exact JSON contracts.
- **Dependency pattern**: reusable functions for shared logic (data loading, settings).
- **Middleware**: cross-cutting behavior (CORS for frontend apps).

---

## 2) High-level migration summary

We migrated the web server layer from Flask to FastAPI while keeping your business logic intact.

### What stayed the same
- Forecasting logic (`inventory_app/forecasting/*`)
- Data loading and preprocessing (`inventory_app/data/*`)
- Stockout calculations and dashboard metrics (`inventory_app/services/*`)
- Jinja template files (`templates/*.html`)
- Simulator service (`simulation_dataset/*`)

### What changed
- Flask app/bootstrap replaced with FastAPI app/bootstrap.
- Flask blueprints replaced with FastAPI routers.
- API responses now use explicit Pydantic schemas.
- Added versioned API namespace (`/api/v1`) for future frontend clients.
- Added CORS support to allow React or other frontend apps later.
- Added modular settings and dependency layers for cleaner architecture.

---

## 3) File-by-file changes and why they matter

## `app.py`

### Before
- Imported Flask app and called `app.run(...)`.

### After
- Imports `uvicorn` and runs ASGI app using `uvicorn.run("app:app", ...)`.

### Why this matters
- FastAPI apps run on ASGI servers (Uvicorn), not Flask's built-in server.
- This is production-aligned behavior for modern Python APIs.

---

## `inventory_app/__init__.py`

### Before
- Created Flask app.
- Registered Flask blueprints.

### After
- Creates `FastAPI(...)` instance.
- Registers CORS middleware.
- Includes routers:
  - `web_router` for server-rendered pages
  - `api_router` for new versioned JSON APIs
  - `legacy_api_router` for backward compatibility

### Why this matters
- App factory is now centralized and framework-correct.
- CORS support makes browser-based frontend integration much easier.
- Routing separation reduces coupling.

---

## `inventory_app/core/settings.py` (new)

### What it does
- Loads environment variables from `.env`.
- Builds a single `Settings` object with all app config.
- Exposes `get_settings()` with caching via `lru_cache`.

### Why this matters
- Configuration is centralized and typed.
- Avoids scattering `os.environ.get(...)` everywhere.
- Easier to test and easier to reason about.

### Key fields for future frontend work
- `cors_origins`
- `host`
- `port`
- `forecast_periods`
- `default_store_id`

---

## `inventory_app/config.py`

### What changed
- Converted to a **compatibility shim**.
- Keeps `Config` class shape so legacy imports won?t break.
- Reads values from new `Settings` source.

### Why this matters
- Smooth migration with minimal break risk.
- Old code paths still function while new architecture is in place.

---

## `inventory_app/dependencies/data.py` (new)

### What it does
- Creates one reusable function to:
  1. build data-source config from settings
  2. load inventory data
  3. preprocess dataframe

### Why this matters
- Removes duplicated data-loading logic from each endpoint.
- Keeps route functions focused on request/response behavior.
- Makes future refactors simpler (single place to change).

---

## `inventory_app/schemas/api.py` (new)

### What it defines
- `HealthResponse`
- `MetricsResponse`
- `ProductForecastResponse`
- `ErrorResponse`

### Why this matters
- These are your API contracts.
- React developers can trust response shape and types.
- FastAPI auto-docs include these schemas, improving cross-team communication.

### Manager-friendly explanation
"We moved from implicit JSON outputs to explicit schema-driven contracts, reducing integration ambiguity and runtime surprises."

---

## `inventory_app/routes/web.py`

### Before
- Flask `Blueprint`
- `render_template(...)`
- `current_app.config`

### After
- FastAPI `APIRouter`
- Starlette/Jinja `TemplateResponse`
- Settings loaded via `get_settings()`

### Important details
- Still renders same pages (`/`, `/product/{product_id}`)
- Still uses your existing `templates/*.html`
- Includes `request` in template context (required by Starlette templates)

### Why this matters
- Frontend behavior remains familiar while backend framework modernizes.
- No forced immediate migration to React.

---

## `inventory_app/routes/api.py`

### Before
- Flask routes under `/api/*`
- Returned `jsonify(...)`
- No response schema enforcement

### After
- FastAPI routers with:
  - `/api/v1/health`
  - `/api/v1/metrics`
  - `/api/v1/forecasts`
  - `/api/v1/forecasts/{product_id}`
- Backward-compatible aliases kept:
  - `/api/metrics`
  - `/api/all-forecasts`

### Additional improvements
- Query params added for flexibility:
  - `store_id`
  - `periods`
- Explicit response models for all key endpoints.
- Error handling through `HTTPException` with status codes (`404`, `503`).

### Why this matters for React
- Predictable, versioned endpoints.
- Easy to consume from Axios/fetch.
- OpenAPI docs become single source of truth for frontend devs.

---

## `inventory_app/routes/__init__.py`

### What changed
- Added exports for router modules.

### Why this matters
- Cleaner imports and clearer route package boundaries.

---

## `requirements.txt`

### Removed
- `Flask`
- `Werkzeug`
- stray `logging` entry (not needed from pip)

### Added
- `fastapi`
- `uvicorn`
- `jinja2`

### Why this matters
- Dependency list now matches runtime architecture.

---

## `README.md`

### What changed
- Updated architecture and run instructions to FastAPI.
- Added API docs path (`/api/docs`).
- Documented versioned endpoints and legacy aliases.
- Explained React readiness and CORS config.

### Why this matters
- Onboarding and handoff documentation now matches actual code.

---

## 4) Architecture now (mental model)

Request flow:
1. Client calls endpoint (web page or JSON API).
2. Route gets `Settings` and shared dataframe dependency.
3. Existing service layer computes forecast/metrics.
4. Route returns:
   - HTML template for server-rendered pages, or
   - Pydantic-validated JSON for API endpoints.

This keeps domain logic separate from HTTP framework concerns.

---

## 5) How this prepares you for React later

### Already done for React readiness
- CORS middleware is configurable (`CORS_ORIGINS`).
- APIs are versioned (`/api/v1/...`).
- Response contracts are typed and documented automatically.
- Store/horizon filters are exposed through query params.

### What you can add later (optional)
- `/api/v1` authentication (JWT/session)
- pagination for large forecast lists
- dedicated DTOs if UI requirements diverge from service outputs
- request IDs / structured logging / tracing

---

## 6) Talking points for your manager

Use this concise narrative:

1. "We modernized the backend from Flask to FastAPI without rewriting core forecasting logic."
2. "We preserved current server-rendered pages, so there is no immediate UI disruption."
3. "We introduced versioned, typed APIs and auto-generated docs to reduce frontend integration risk."
4. "We added modular settings and shared dependencies to lower maintenance cost."
5. "The architecture now supports phased adoption of React rather than a risky big-bang rewrite."

---

## 7) Run and verify checklist

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start app:
```bash
python app.py
```

3. Verify:
- `http://localhost:8000/` (dashboard)
- `http://localhost:8000/product/<product_id>` (detail page)
- `http://localhost:8000/api/docs` (OpenAPI docs)
- `http://localhost:8000/api/v1/health` (health check)

---

## 8) Practical differences: Flask vs FastAPI (quick comparison)

- Flask: lightweight, manual patterns, flexible but less opinionated for API typing.
- FastAPI: typed-first, schema-first, automatic docs, better default path for API-heavy systems.

In your project, this means less ambiguity between backend and frontend teams, and cleaner scaling path.

---

## 9) Notes about migration safety

- Legacy routes were preserved so existing consumers are not broken immediately.
- Business logic modules were intentionally not rewritten to reduce regression risk.
- Migration focused on transport layer (framework/routing/contracts), not forecasting math.

This is the safest pattern for framework migration in production-like projects.
