import logging
import os
import time
from datetime import UTC, date, datetime

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from market_universe import ALL_TICKERS, SECTOR_MAP
from runtime_guard import validate_runtime
from sql_loader import load_sql

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

UPSERT_MARKET_PRICE_SQL = text(load_sql("daily_refresh/upsert_market_price.sql"))


def utc_now():
    return datetime.now(UTC)


def refresh_ticker(ticker: str) -> int:
    try:
        history = yf.Ticker(ticker).history(period="5d", auto_adjust=False)
        if history is None or history.empty:
            logger.warning("No data returned for %s", ticker)
            return 0

        df = history.reset_index()
        df.columns = [column.lower().replace(" ", "_") for column in df.columns]
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["ticker"] = ticker
        df["sector"] = SECTOR_MAP.get(ticker, "Unknown")
        df["loaded_at"] = utc_now()
        df = df.dropna(subset=["close"])

        if df.empty:
            logger.warning("No usable close prices found for %s", ticker)
            return 0

        processed_rows = 0
        with engine.begin() as conn:
            for _, row in df.iterrows():
                conn.execute(
                    UPSERT_MARKET_PRICE_SQL,
                    {
                        "ticker": ticker,
                        "sector": SECTOR_MAP.get(ticker, "Unknown"),
                        "date": row["date"],
                        "open": float(row["open"]) if pd.notna(row.get("open")) else None,
                        "high": float(row["high"]) if pd.notna(row.get("high")) else None,
                        "low": float(row["low"]) if pd.notna(row.get("low")) else None,
                        "close": float(row["close"]) if pd.notna(row.get("close")) else None,
                        "adj_close": float(row["adj_close"]) if pd.notna(row.get("adj_close")) else None,
                        "volume": int(row["volume"]) if pd.notna(row.get("volume")) else None,
                        "loaded_at": row["loaded_at"],
                    },
                )
                processed_rows += 1
        return processed_rows
    except Exception as exc:
        logger.error("Failed to refresh %s: %s", ticker, exc)
        return 0


def run_daily_refresh():
    validate_runtime()
    logger.info("Daily refresh for %s", date.today())
    logger.info("%s", "=" * 50)

    total_rows = 0
    for ticker in ALL_TICKERS:
        rows = refresh_ticker(ticker)
        if rows > 0:
            logger.info("%s %s rows processed", f"{ticker:<22}", rows)
        total_rows += rows
        time.sleep(0.3)

    logger.info("Refresh complete. %s rows processed.", total_rows)


if __name__ == "__main__":
    run_daily_refresh()
