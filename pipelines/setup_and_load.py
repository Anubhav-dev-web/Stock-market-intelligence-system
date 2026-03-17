import logging
import os
import time
from datetime import UTC, datetime, timedelta

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from market_universe import UNIVERSE
from runtime_guard import validate_runtime
from sql_loader import load_sql

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

INSERT_MARKET_PRICE_SQL = text(load_sql("setup_and_load/insert_market_price.sql"))
LOAD_SUMMARY_SQL = text(load_sql("setup_and_load/load_summary.sql"))


def utc_now():
    return datetime.now(UTC)


def create_schema():
    with engine.begin() as conn:
        conn.execute(text(load_sql("setup_and_load/create_schema.sql")))
    logger.info("Schema and table created successfully")

    with engine.connect() as conn:
        exists = conn.execute(text(load_sql("setup_and_load/check_table_exists.sql"))).scalar()
    logger.info("Table exists check: %s", bool(exists))


def load_ticker(ticker: str, sector: str, start: str, end: str) -> int:
    try:
        history = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
        if history is None or history.empty:
            logger.warning("No data returned for %s", ticker)
            return 0

        df = history.reset_index()
        df.columns = [column.lower().replace(" ", "_") for column in df.columns]
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["ticker"] = ticker
        df["sector"] = sector
        df["loaded_at"] = utc_now()
        df = df.dropna(subset=["close"])

        if df.empty:
            logger.warning("No usable close prices found for %s", ticker)
            return 0

        inserted = 0
        with engine.begin() as conn:
            for _, row in df.iterrows():
                try:
                    conn.execute(
                        INSERT_MARKET_PRICE_SQL,
                        {
                            "ticker": ticker,
                            "sector": sector,
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
                    inserted += 1
                except Exception as row_error:
                    logger.debug("Skipped one row for %s: %s", ticker, row_error)
        return inserted
    except Exception as exc:
        logger.error("Failed to load %s: %s", ticker, exc)
        return 0


def run_load():
    validate_runtime()
    end_date = utc_now().strftime("%Y-%m-%d")
    start_date = (utc_now() - timedelta(days=2 * 365)).strftime("%Y-%m-%d")

    logger.info("Loading 2 years of history: %s to %s", start_date, end_date)
    logger.info("%s", "=" * 60)

    total_rows = 0
    failed_tickers = []

    for sector, tickers in UNIVERSE.items():
        logger.info("Sector: %s", sector)
        for ticker in tickers:
            rows = load_ticker(ticker, sector, start_date, end_date)
            if rows > 0:
                logger.info("  %s %s rows", f"{ticker:<22}", f"{rows:>5,}")
            else:
                failed_tickers.append(ticker)
            total_rows += rows
            time.sleep(0.4)

    logger.info("%s", "=" * 60)
    logger.info("Load complete. Total rows inserted: %s", f"{total_rows:,}")
    if failed_tickers:
        logger.warning("Tickers with no inserted rows: %s", failed_tickers)

    with engine.connect() as conn:
        result = conn.execute(LOAD_SUMMARY_SQL)
        logger.info("Database summary")
        logger.info("%-12s %8s %8s %12s %12s", "Sector", "Tickers", "Rows", "From", "To")
        logger.info("%s", "-" * 55)
        for row in result:
            logger.info(
                "%-12s %8s %8s %12s %12s",
                row[0],
                row[1],
                f"{row[2]:,}",
                str(row[3]),
                str(row[4]),
            )


if __name__ == "__main__":
    create_schema()
    run_load()
