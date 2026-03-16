# setup_and_load.py
# Run this ONCE — creates DB schema then loads all data

import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os, time, logging
from sql_loader import load_sql

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# ── STEP 1: Create schema and table ──────────────────────────────────────────
def create_schema():
    with engine.begin() as conn:
        conn.execute(text(load_sql('setup_and_load/create_schema.sql')))
    logger.info("✓ Schema and table created successfully")

    # Verify
    with engine.connect() as conn:
        result = conn.execute(text(load_sql('setup_and_load/check_table_exists.sql')))
        exists = result.scalar()
        logger.info(f"✓ Table exists check: {bool(exists)}")

# ── STEP 2: Universe ─────────────────────────────────────────────────────────
UNIVERSE = {
    'IT': [
        'TCS.NS','INFY.NS','WIPRO.NS','HCLTECH.NS','TECHM.NS',
        'LTIM.NS','MPHASIS.NS','PERSISTENT.NS','COFORGE.NS','OFSS.NS'
    ],
    'Banking': [
        'HDFCBANK.NS','ICICIBANK.NS','KOTAKBANK.NS','SBIN.NS','AXISBANK.NS',
        'BAJFINANCE.NS','BAJAJFINSV.NS','INDUSINDBK.NS','PNB.NS','HDFCLIFE.NS'
    ],
    'Pharma': [
        'SUNPHARMA.NS','DRREDDY.NS','CIPLA.NS','DIVISLAB.NS','APOLLOHOSP.NS',
        'TORNTPHARM.NS','AUROPHARMA.NS','LUPIN.NS','BIOCON.NS','MAXHEALTH.NS'
    ],
    'Energy': [
        'RELIANCE.NS','ONGC.NS','NTPC.NS','POWERGRID.NS','IOC.NS',
        'ADANIGREEN.NS','TATAPOWER.NS','COALINDIA.NS','BPCL.NS','ADANIPORTS.NS'
    ],
    'FMCG': [
        'HINDUNILVR.NS','ITC.NS','NESTLEIND.NS','BRITANNIA.NS','DABUR.NS',
        'MARICO.NS','GODREJCP.NS','COLPAL.NS','EMAMILTD.NS','TATACONSUM.NS'
    ],
    'Commodity': ['GC=F','CL=F','SI=F'],
    'Index':     ['^NSEI','^BSESN','^NSEBANK','^CNXIT','^INDIAVIX','USDINR=X']
}

# ── STEP 3: Load one ticker ───────────────────────────────────────────────────
def load_ticker(ticker: str, sector: str, start: str, end: str) -> int:
    try:
        t  = yf.Ticker(ticker)
        df = t.history(start=start, end=end, auto_adjust=False)

        if df is None or df.empty:
            logger.warning(f"  ⚠  No data: {ticker}")
            return 0

        df.reset_index(inplace=True)
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        df['date']      = pd.to_datetime(df['date']).dt.date
        df['ticker']    = ticker
        df['sector']    = sector
        df['loaded_at'] = datetime.now()
        df = df.dropna(subset=['close'])

        if df.empty:
            return 0

        insert_sql = load_sql('setup_and_load/insert_market_price.sql')
        inserted = 0
        with engine.begin() as conn:
            for _, row in df.iterrows():
                try:
                    conn.execute(text(insert_sql), {
                        'ticker':    ticker,
                        'sector':    sector,
                        'date':      row['date'],
                        'open':      float(row['open'])      if pd.notna(row.get('open'))      else None,
                        'high':      float(row['high'])      if pd.notna(row.get('high'))      else None,
                        'low':       float(row['low'])       if pd.notna(row.get('low'))       else None,
                        'close':     float(row['close'])     if pd.notna(row.get('close'))     else None,
                        'adj_close': float(row['adj_close']) if pd.notna(row.get('adj_close')) else None,
                        'volume':    int(row['volume'])      if pd.notna(row.get('volume'))    else None,
                        'loaded_at': row['loaded_at'],
                    })
                    inserted += 1
                except Exception as row_err:
                    logger.debug(f"    Row skip: {row_err}")
        return inserted

    except Exception as e:
        logger.error(f"  ✗  {ticker}: {e}")
        return 0

# ── STEP 4: Run full load ─────────────────────────────────────────────────────
def run_load():
    end   = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')

    logger.info(f"\nLoading 2 years: {start} → {end}")
    logger.info("=" * 60)

    total = 0
    failed = []

    for sector, tickers in UNIVERSE.items():
        logger.info(f"\n── {sector} ──")
        for ticker in tickers:
            rows = load_ticker(ticker, sector, start, end)
            if rows > 0:
                logger.info(f"  ✓  {ticker:<22} {rows:>5,} rows")
            else:
                logger.warning(f"  ⚠  {ticker:<22}     0 rows")
                failed.append(ticker)
            total += rows
            time.sleep(0.4)

    logger.info(f"\n{'='*60}")
    logger.info(f"COMPLETE — Total rows: {total:,}")
    if failed:
        logger.warning(f"Failed tickers: {failed}")

    # Final summary from DB
    with engine.connect() as conn:
        result = conn.execute(text(load_sql('setup_and_load/load_summary.sql')))
        logger.info("\n── DB Summary ──")
        logger.info(f"{'Sector':<12} {'Tickers':>8} {'Rows':>8} {'From':>12} {'To':>12}")
        logger.info("-" * 55)
        for r in result:
            logger.info(f"{r[0]:<12} {r[1]:>8} {r[2]:>8,} {str(r[3]):>12} {str(r[4]):>12}")


if __name__ == '__main__':
    create_schema()   # creates table first
    run_load()        # then loads data