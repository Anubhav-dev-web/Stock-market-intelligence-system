import logging
import os

import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from runtime_guard import validate_runtime
from sql_loader import load_sql

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

RAW_FLOAT_COLUMNS = ["open", "high", "low", "close", "adj_close"]
RAW_INTEGER_COLUMNS = ["volume", "company_key"]


def load_dataframe(relative_path):
    query = text(load_sql(relative_path))
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()
    return pd.DataFrame(rows)


def normalize_raw_dataframe(df):
    for column in RAW_FLOAT_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in RAW_INTEGER_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def insert_fact_rows(df, chunk_size=1000):
    insert_sql = text(load_sql("compute_indicators/insert_fct_daily_prices.sql"))
    clean_df = df.replace([np.inf, -np.inf], np.nan)
    records = clean_df.where(pd.notna(clean_df), None).to_dict(orient="records")

    with engine.begin() as conn:
        for start in range(0, len(records), chunk_size):
            batch = records[start:start + chunk_size]
            conn.execute(insert_sql, batch)


def trend_signal(row):
    if pd.isna(row["close"]) or pd.isna(row["ma_20"]) or pd.isna(row["ma_50"]):
        return "Neutral"
    if row["close"] > row["ma_20"] > row["ma_50"] > row["ma_200"]:
        return "Strong Bullish"
    if row["close"] > row["ma_20"] > row["ma_50"]:
        return "Bullish"
    if row["close"] < row["ma_20"] < row["ma_50"] < row["ma_200"]:
        return "Strong Bearish"
    if row["close"] < row["ma_20"] < row["ma_50"]:
        return "Bearish"
    return "Neutral"


def compute_and_load():
    validate_runtime()
    logger.info("Loading raw prices...")
    df = normalize_raw_dataframe(load_dataframe("compute_indicators/load_raw_prices.sql"))
    if df.empty:
        logger.warning("No raw prices were found. Run pipelines/setup_and_load.py first.")
        return

    logger.info("Loaded %s rows for %s tickers", f"{len(df):,}", df["ticker"].nunique())

    missing_company_keys = sorted(df.loc[df["company_key"].isna(), "ticker"].unique().tolist())
    if missing_company_keys:
        logger.warning("Missing company_key values for tickers: %s", missing_company_keys)

    results = []
    for ticker, group in df.groupby("ticker", sort=True):
        group = group.sort_values("date").copy()

        group["daily_return_pct"] = group["close"].pct_change() * 100
        group["weekly_return_pct"] = group["close"].pct_change(5) * 100
        group["monthly_return_pct"] = group["close"].pct_change(21) * 100

        group["ma_20"] = group["close"].rolling(20).mean()
        group["ma_50"] = group["close"].rolling(50).mean()
        group["ma_200"] = group["close"].rolling(200).mean()

        rolling_mean = group["close"].rolling(20)
        group["bb_upper"] = rolling_mean.mean() + 2 * rolling_mean.std()
        group["bb_lower"] = rolling_mean.mean() - 2 * rolling_mean.std()

        delta = group["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-10)
        group["rsi_14"] = 100 - (100 / (1 + rs))

        group["high_52w"] = group["high"].rolling(252, min_periods=1).max()
        group["low_52w"] = group["low"].rolling(252, min_periods=1).min()
        group["pct_from_52w_high"] = (
            (group["close"] - group["high_52w"]) / group["high_52w"] * 100
        )

        group["trend_signal"] = group.apply(trend_signal, axis=1)
        group["rsi_zone"] = group["rsi_14"].apply(
            lambda value: (
                "Overbought"
                if value >= 70
                else "Oversold" if value <= 30 else "Neutral"
            )
            if pd.notna(value)
            else "Neutral"
        )
        group["date_key"] = pd.to_datetime(group["date"]).dt.strftime("%Y%m%d").astype(int)

        results.append(group)
        logger.info("Computed indicators for %s", ticker)

    final = pd.concat(results, ignore_index=True)
    if not missing_company_keys:
        final["company_key"] = final["company_key"].astype(int)

    final = final[
        [
            "ticker",
            "date_key",
            "company_key",
            "open",
            "high",
            "low",
            "close",
            "adj_close",
            "volume",
            "daily_return_pct",
            "weekly_return_pct",
            "monthly_return_pct",
            "ma_20",
            "ma_50",
            "ma_200",
            "bb_upper",
            "bb_lower",
            "rsi_14",
            "high_52w",
            "low_52w",
            "pct_from_52w_high",
            "trend_signal",
            "rsi_zone",
        ]
    ].rename(
        columns={
            "open": "open_price",
            "high": "high_price",
            "low": "low_price",
            "close": "close_price",
        }
    )

    logger.info("Refreshing analytics.fct_daily_prices with %s rows...", f"{len(final):,}")
    with engine.begin() as conn:
        conn.execute(text(load_sql("compute_indicators/truncate_fct.sql")))

    insert_fact_rows(final)

    with engine.connect() as conn:
        fact_rows = conn.execute(text(load_sql("compute_indicators/count_fct.sql"))).scalar()
        trend_summary = conn.execute(text(load_sql("compute_indicators/trend_summary.sql"))).all()
        rsi_summary = conn.execute(text(load_sql("compute_indicators/rsi_summary.sql"))).all()

    logger.info("Fact table rows: %s", f"{fact_rows:,}")
    logger.info("Trend summary:")
    for trend, count in trend_summary:
        logger.info("  %-16s %s", trend, f"{count:,}")

    logger.info("RSI summary:")
    for zone, count in rsi_summary:
        logger.info("  %-16s %s", zone, f"{count:,}")


if __name__ == "__main__":
    compute_and_load()
