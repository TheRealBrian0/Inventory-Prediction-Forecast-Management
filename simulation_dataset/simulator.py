"""Independent inventory data simulator for MySQL.

Generates one new logical day of data for all configured warehouses/products
every N real-world seconds (default: 180).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib import error as url_error
from urllib import request as url_request

import pymysql
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
SIM_DIR = Path(__file__).resolve().parent
ROOT_ENV_PATH = ROOT_DIR / ".env"
SIM_ENV_PATH = SIM_DIR / ".env"

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d")
DEFAULT_WAREHOUSES = ("S001", "S002", "S003", "S004", "S005")

WAREHOUSE_REGION_MAP = {
    "S001": "North",
    "S002": "South",
    "S003": "East",
    "S004": "West",
    "S005": "Central",
}

WEATHER_OPTIONS = {
    "North": ["Snowy", "Cloudy", "Rainy", "Windy"],
    "South": ["Sunny", "Humid", "Cloudy", "Rainy"],
    "East": ["Rainy", "Cloudy", "Windy", "Sunny"],
    "West": ["Dry", "Sunny", "Windy", "Cloudy"],
    "Central": ["Sunny", "Cloudy", "Rainy", "Windy"],
}


@dataclass
class SimulatorConfig:
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    db_table: str
    warehouses: tuple[str, ...]
    interval_seconds: int
    use_ollama: bool
    ollama_host: str
    ollama_model: str


class SimulationError(RuntimeError):
    """Raised when simulation cannot proceed."""


def load_environment() -> None:
    """Load root env first, then simulator-specific overrides."""
    if ROOT_ENV_PATH.exists():
        load_dotenv(ROOT_ENV_PATH)
    if SIM_ENV_PATH.exists():
        load_dotenv(SIM_ENV_PATH, override=True)


def build_config(interval_override: int | None = None, use_ollama_override: bool | None = None) -> SimulatorConfig:
    warehouses_env = os.getenv("SIM_WAREHOUSE_IDS", ",".join(DEFAULT_WAREHOUSES))
    warehouses = tuple(w.strip() for w in warehouses_env.split(",") if w.strip())
    if not warehouses:
        warehouses = DEFAULT_WAREHOUSES

    interval_seconds = int(os.getenv("SIM_INTERVAL_SECONDS", "180"))
    if interval_override is not None:
        interval_seconds = interval_override

    use_ollama = os.getenv("SIM_USE_OLLAMA", "1").strip() not in ("0", "false", "False")
    if use_ollama_override is not None:
        use_ollama = use_ollama_override

    return SimulatorConfig(
        db_host=os.getenv("DB_HOST", "127.0.0.1"),
        db_port=int(os.getenv("DB_PORT", "3306")),
        db_user=os.getenv("DB_USER", "root"),
        db_password=os.getenv("DB_PASSWORD", "root"),
        db_name=os.getenv("DB_NAME", "sysco_poc_db"),
        db_table=os.getenv("DB_TABLE", "retail_inventory"),
        warehouses=warehouses,
        interval_seconds=max(5, interval_seconds),
        use_ollama=use_ollama,
        ollama_host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2:latest"),
    )


def connect_db(cfg: SimulatorConfig):
    return pymysql.connect(
        host=cfg.db_host,
        port=cfg.db_port,
        user=cfg.db_user,
        password=cfg.db_password,
        database=cfg.db_name,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )


def parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def fetch_latest_date(cursor, table: str) -> date:
    cursor.execute(f"SELECT `date` FROM `{table}`")
    latest: date | None = None
    for row in cursor.fetchall():
        parsed = parse_date(row.get("date"))
        if parsed and (latest is None or parsed > latest):
            latest = parsed
    if latest is None:
        raise SimulationError("Unable to resolve latest date from source table.")
    return latest


def fetch_products(cursor, table: str) -> list[str]:
    cursor.execute(f"SELECT DISTINCT `product_id` AS product_id FROM `{table}` ORDER BY `product_id`")
    products = [row["product_id"] for row in cursor.fetchall() if row.get("product_id")]
    if not products:
        raise SimulationError("No products found in source table.")
    return products


def fetch_product_templates(cursor, table: str, latest_date_text: str, products: list[str]) -> dict[str, dict[str, Any]]:
    cursor.execute(
        f"""
        SELECT
            `date`, `store_id`, `product_id`, `category`, `region`,
            `inventory_level`, `units_sold`, `units_ordered`,
            `demand_forecast`, `price`, `discount`, `weather_condition`,
            `holiday_promotion`, `competitor_pricing`, `seasonality`
        FROM `{table}`
        WHERE `date` = %s
        """,
        (latest_date_text,),
    )
    rows = cursor.fetchall()
    templates: dict[str, dict[str, Any]] = {}
    for row in rows:
        product_id = row.get("product_id")
        if product_id and product_id not in templates:
            templates[product_id] = row

    missing = [p for p in products if p not in templates]
    for product_id in missing:
        cursor.execute(
            f"""
            SELECT
                `date`, `store_id`, `product_id`, `category`, `region`,
                `inventory_level`, `units_sold`, `units_ordered`,
                `demand_forecast`, `price`, `discount`, `weather_condition`,
                `holiday_promotion`, `competitor_pricing`, `seasonality`
            FROM `{table}`
            WHERE `product_id` = %s
            """,
            (product_id,),
        )
        candidate_rows = cursor.fetchall()
        best_row = None
        best_date = None
        for row in candidate_rows:
            row_date = parse_date(row.get("date"))
            if row_date and (best_date is None or row_date > best_date):
                best_date = row_date
                best_row = row
        if best_row:
            templates[product_id] = best_row

    missing_after = [p for p in products if p not in templates]
    if missing_after:
        raise SimulationError(f"Missing templates for products: {missing_after[:5]} ...")
    return templates


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def default_signal(seed_key: str) -> dict[str, float]:
    rng = random.Random(seed_key)
    return {
        "demand_shift": rng.uniform(-0.18, 0.26),
        "inventory_shift": rng.uniform(-0.22, 0.22),
        "promo_boost": rng.uniform(0.05, 0.40),
        "volatility": rng.uniform(0.10, 0.35),
    }


def parse_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def fetch_ollama_signal(cfg: SimulatorConfig, target_date: date) -> dict[str, float]:
    seed_key = f"{target_date.isoformat()}:{cfg.ollama_model}"
    fallback = default_signal(seed_key)
    if not cfg.use_ollama:
        return fallback

    prompt = (
        "You are helping simulate retail demand. Return STRICT JSON only with keys: "
        "demand_shift, inventory_shift, promo_boost, volatility. "
        "Ranges: demand_shift [-0.35,0.35], inventory_shift [-0.35,0.35], "
        "promo_boost [0,1], volatility [0.05,0.5]. "
        f"Target business date: {target_date.isoformat()}."
    )
    payload = {
        "model": cfg.ollama_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    req = url_request.Request(
        url=f"{cfg.ollama_host}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with url_request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (url_error.URLError, TimeoutError, json.JSONDecodeError):
        return fallback

    response_text = str(data.get("response", "")).strip()
    parsed = parse_json_object(response_text)
    if not parsed:
        return fallback

    return {
        "demand_shift": clamp(float(parsed.get("demand_shift", fallback["demand_shift"])), -0.35, 0.35),
        "inventory_shift": clamp(float(parsed.get("inventory_shift", fallback["inventory_shift"])), -0.35, 0.35),
        "promo_boost": clamp(float(parsed.get("promo_boost", fallback["promo_boost"])), 0.0, 1.0),
        "volatility": clamp(float(parsed.get("volatility", fallback["volatility"])), 0.05, 0.5),
    }


def season_label(target_date: date) -> str:
    month = target_date.month
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    return "Autumn"


def choose_status_cover_days(rng: random.Random) -> tuple[str, int]:
    roll = rng.random()
    if roll < 0.33:
        return "critical", rng.randint(1, 4)
    if roll < 0.68:
        return "warning", rng.randint(5, 12)
    return "healthy", rng.randint(14, 35)


def generate_rows_for_day(
    cfg: SimulatorConfig,
    target_date: date,
    products: list[str],
    templates: dict[str, dict[str, Any]],
    signal: dict[str, float],
) -> list[tuple[Any, ...]]:
    rows: list[tuple[Any, ...]] = []
    season = season_label(target_date)

    for warehouse_index, warehouse_id in enumerate(cfg.warehouses):
        region = WAREHOUSE_REGION_MAP.get(warehouse_id, "Unknown")
        weather_pool = WEATHER_OPTIONS.get(region, ["Cloudy", "Sunny"])
        store_factor = 0.88 + (warehouse_index * 0.08)

        for product_id in products:
            template = templates[product_id]
            key = f"{target_date.isoformat()}:{warehouse_id}:{product_id}"
            rng = random.Random(key)

            demand_anchor = float(template.get("units_sold") or template.get("demand_forecast") or 20)
            price_anchor = float(template.get("price") or 10.0)

            # Diverse statuses by SKU/store/day to exercise downstream forecast behavior.
            status, cover_days = choose_status_cover_days(rng)
            cover_days = int(
                max(
                    1,
                    round(
                        cover_days
                        * (1.0 - 0.55 * signal["inventory_shift"])
                        * (1.0 + rng.uniform(-0.12, 0.12))
                    ),
                )
            )

            demand_multiplier = (
                store_factor
                * (1.0 + signal["demand_shift"])
                * (1.0 + signal["promo_boost"] * 0.25)
                * (1.0 + rng.uniform(-signal["volatility"], signal["volatility"]))
            )
            units_sold = int(max(1, round(demand_anchor * demand_multiplier)))
            demand_forecast = round(max(0.0, units_sold * (1.0 + rng.uniform(-0.16, 0.28))), 2)

            inventory_noise = rng.randint(-25, 60)
            inventory_level = int(max(0, round(units_sold * cover_days + inventory_noise)))

            base_reorder = units_sold * rng.uniform(0.2, 1.2)
            if status == "critical":
                base_reorder *= rng.uniform(1.4, 2.3)
            elif status == "warning":
                base_reorder *= rng.uniform(1.0, 1.6)
            units_ordered = int(max(0, round(base_reorder)))

            holiday_promotion = 1 if rng.random() < signal["promo_boost"] * 0.35 else 0
            discount = int(max(0, min(45, round(rng.uniform(0, 22) + holiday_promotion * 10))))
            weather_condition = rng.choice(weather_pool)
            competitor_pricing = round(max(0.01, price_anchor * (1.0 + rng.uniform(-0.14, 0.11))), 2)

            rows.append(
                (
                    target_date.isoformat(),
                    warehouse_id,
                    product_id,
                    str(template.get("category") or "General"),
                    region,
                    inventory_level,
                    units_sold,
                    units_ordered,
                    demand_forecast,
                    round(price_anchor, 2),
                    discount,
                    weather_condition,
                    holiday_promotion,
                    competitor_pricing,
                    season,
                )
            )
    return rows


def insert_rows(cursor, table: str, rows: list[tuple[Any, ...]]) -> None:
    query = f"""
    INSERT INTO `{table}` (
        `date`,
        `store_id`,
        `product_id`,
        `category`,
        `region`,
        `inventory_level`,
        `units_sold`,
        `units_ordered`,
        `demand_forecast`,
        `price`,
        `discount`,
        `weather_condition`,
        `holiday_promotion`,
        `competitor_pricing`,
        `seasonality`
    ) VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s
    )
    """
    cursor.executemany(query, rows)


def run_single_cycle(cfg: SimulatorConfig) -> dict[str, Any]:
    with connect_db(cfg) as conn:
        with conn.cursor() as cursor:
            latest_date = fetch_latest_date(cursor, cfg.db_table)
            next_date = latest_date + timedelta(days=1)
            next_date_text = next_date.isoformat()

            cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{cfg.db_table}` WHERE `date` = %s", (next_date_text,))
            existing = int(cursor.fetchone()["cnt"])
            if existing > 0:
                conn.rollback()
                return {
                    "inserted": 0,
                    "latest_date": latest_date.isoformat(),
                    "next_date": next_date_text,
                    "reason": "next_date_exists",
                }

            products = fetch_products(cursor, cfg.db_table)
            templates = fetch_product_templates(cursor, cfg.db_table, latest_date.isoformat(), products)
            signal = fetch_ollama_signal(cfg, next_date)
            rows = generate_rows_for_day(cfg, next_date, products, templates, signal)
            insert_rows(cursor, cfg.db_table, rows)
            conn.commit()

            return {
                "inserted": len(rows),
                "latest_date": latest_date.isoformat(),
                "next_date": next_date_text,
                "products": len(products),
                "warehouses": len(cfg.warehouses),
                "signal": signal,
            }


def setup_logging() -> None:
    log_path = SIM_DIR / "simulator.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retail inventory simulator (independent service).")
    parser.add_argument("--once", action="store_true", help="Generate one new day and exit.")
    parser.add_argument("--loop", action="store_true", help="Run continuously every interval.")
    parser.add_argument("--interval-seconds", type=int, default=None, help="Loop interval in seconds (default from env).")
    parser.add_argument("--disable-ollama", action="store_true", help="Disable Ollama signal generation and use local fallback.")
    return parser.parse_args()


def main() -> int:
    load_environment()
    setup_logging()
    args = parse_args()
    run_loop = args.loop or not args.once

    cfg = build_config(
        interval_override=args.interval_seconds,
        use_ollama_override=(False if args.disable_ollama else None),
    )

    logging.info(
        "Simulator config: db=%s.%s warehouses=%s interval=%ss ollama=%s(%s)",
        cfg.db_name,
        cfg.db_table,
        ",".join(cfg.warehouses),
        cfg.interval_seconds,
        "on" if cfg.use_ollama else "off",
        cfg.ollama_model,
    )

    if not run_loop:
        result = run_single_cycle(cfg)
        logging.info("Cycle result: %s", result)
        return 0

    while True:
        try:
            result = run_single_cycle(cfg)
            logging.info("Cycle result: %s", result)
        except Exception as exc:
            logging.exception("Cycle failed: %s", exc)

        time.sleep(cfg.interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
