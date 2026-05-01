# import os

# from dotenv import load_dotenv
# from sqlalchemy import create_engine, text

# from sql_loader import load_sql

# load_dotenv()
# engine = create_engine(
#     f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
#     f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
# )

# with engine.connect() as conn:
#     result = conn.execute(text(load_sql("test/sector_summary.sql")))
#     print(f"\n{'Sector':<12} {'Tickers':>8} {'Rows':>10} {'From':>12} {'To':>12}")
#     print("-" * 58)
#     for row in result:
#         print(f"{row[0]:<12} {row[1]:>8} {row[2]:>10,} {str(row[3]):>12} {str(row[4]):>12}")


# check_db.py
# from sqlalchemy import create_engine, text
# from dotenv import load_dotenv
# import os

# load_dotenv()

# engine = create_engine(
#     f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
#     f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
# )

# with engine.connect() as conn:
#     r = conn.execute(text('SELECT COUNT(*) FROM analytics.fct_daily_prices'))
#     print(f'Rows in fct: {r.scalar():,}')

#     r = conn.execute(text('SELECT MAX(date_key) FROM analytics.fct_daily_prices'))
#     print(f'Latest date: {r.scalar()}')

#     r = conn.execute(text('SELECT COUNT(DISTINCT ticker) FROM analytics.fct_daily_prices'))
#     print(f'Tickers: {r.scalar()}')

#     r = conn.execute(text('SELECT COUNT(*) FROM raw.market_prices'))
#     print(f'Raw rows: {r.scalar():,}')


# # run in Windows terminal (venv activated)
# import yfinance as yf
# t = yf.Ticker('HDFCBANK.NS')
# df = t.history(period='5d', auto_adjust=False)
# print(df[['Open','High','Low','Close','Volume']].tail())

# backfill_gap.py
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os, logging

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger(__name__)

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

TICKERS = [
    'TCS.NS','INFY.NS','WIPRO.NS','HCLTECH.NS','TECHM.NS',
    'LTIM.NS','MPHASIS.NS','PERSISTENT.NS','COFORGE.NS','OFSS.NS',
    'HDFCBANK.NS','ICICIBANK.NS','KOTAKBANK.NS','SBIN.NS','AXISBANK.NS',
    'BAJFINANCE.NS','BAJAJFINSV.NS','INDUSINDBK.NS','PNB.NS','HDFCLIFE.NS',
    'SUNPHARMA.NS','DRREDDY.NS','CIPLA.NS','DIVISLAB.NS','APOLLOHOSP.NS',
    'TORNTPHARM.NS','AUROPHARMA.NS','LUPIN.NS','BIOCON.NS','MAXHEALTH.NS',
    'RELIANCE.NS','ONGC.NS','NTPC.NS','POWERGRID.NS','IOC.NS',
    'ADANIGREEN.NS','TATAPOWER.NS','COALINDIA.NS','BPCL.NS','ADANIPORTS.NS',
    'HINDUNILVR.NS','ITC.NS','NESTLEIND.NS','BRITANNIA.NS','DABUR.NS',
    'MARICO.NS','GODREJCP.NS','COLPAL.NS','EMAMILTD.NS','TATACONSUM.NS',
    'GC=F','CL=F','SI=F',
    '^NSEI','^BSESN','^NSEBANK','^CNXIT','^INDIAVIX','USDINR=X'
]

SECTOR_MAP = {
    'TCS.NS':'IT','INFY.NS':'IT','WIPRO.NS':'IT','HCLTECH.NS':'IT',
    'TECHM.NS':'IT','LTIM.NS':'IT','MPHASIS.NS':'IT','PERSISTENT.NS':'IT',
    'COFORGE.NS':'IT','OFSS.NS':'IT',
    'HDFCBANK.NS':'Banking','ICICIBANK.NS':'Banking','KOTAKBANK.NS':'Banking',
    'SBIN.NS':'Banking','AXISBANK.NS':'Banking','BAJFINANCE.NS':'Banking',
    'BAJAJFINSV.NS':'Banking','INDUSINDBK.NS':'Banking','PNB.NS':'Banking',
    'HDFCLIFE.NS':'Banking',
    'SUNPHARMA.NS':'Pharma','DRREDDY.NS':'Pharma','CIPLA.NS':'Pharma',
    'DIVISLAB.NS':'Pharma','APOLLOHOSP.NS':'Pharma','TORNTPHARM.NS':'Pharma',
    'AUROPHARMA.NS':'Pharma','LUPIN.NS':'Pharma','BIOCON.NS':'Pharma',
    'MAXHEALTH.NS':'Pharma',
    'RELIANCE.NS':'Energy','ONGC.NS':'Energy','NTPC.NS':'Energy',
    'POWERGRID.NS':'Energy','IOC.NS':'Energy','ADANIGREEN.NS':'Energy',
    'TATAPOWER.NS':'Energy','COALINDIA.NS':'Energy','BPCL.NS':'Energy',
    'ADANIPORTS.NS':'Energy',
    'HINDUNILVR.NS':'FMCG','ITC.NS':'FMCG','NESTLEIND.NS':'FMCG',
    'BRITANNIA.NS':'FMCG','DABUR.NS':'FMCG','MARICO.NS':'FMCG',
    'GODREJCP.NS':'FMCG','COLPAL.NS':'FMCG','EMAMILTD.NS':'FMCG',
    'TATACONSUM.NS':'FMCG',
    'GC=F':'Commodity','CL=F':'Commodity','SI=F':'Commodity',
    '^NSEI':'Index','^BSESN':'Index','^NSEBANK':'Index',
    '^CNXIT':'Index','^INDIAVIX':'Index','USDINR=X':'Index',
}

def backfill(ticker, sector, start='2026-03-01', end='2026-05-02'):
    try:
        t = yf.Ticker(ticker)
        df = t.history(start=start, end=end, auto_adjust=False)
        if df is None or df.empty:
            logger.warning(f"No data: {ticker}")
            return 0

        df.reset_index(inplace=True)
        df.columns = [c.lower().replace(' ','_') for c in df.columns]
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['ticker'] = ticker
        df['sector'] = sector
        df = df.dropna(subset=['close'])

        inserted = 0
        with engine.begin() as conn:
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO raw.market_prices
                        (ticker, sector, date, open, high, low,
                         close, adj_close, volume)
                    VALUES
                        (:ticker, :sector, :date, :open, :high, :low,
                         :close, :adj_close, :volume)
                    ON CONFLICT (ticker, date) DO UPDATE SET
                        open=EXCLUDED.open, high=EXCLUDED.high,
                        low=EXCLUDED.low,   close=EXCLUDED.close,
                        adj_close=EXCLUDED.adj_close,
                        volume=EXCLUDED.volume
                """), {
                    'ticker':    ticker,
                    'sector':    sector,
                    'date':      row['date'],
                    'open':      float(row['open'])      if pd.notna(row.get('open'))      else None,
                    'high':      float(row['high'])      if pd.notna(row.get('high'))      else None,
                    'low':       float(row['low'])       if pd.notna(row.get('low'))       else None,
                    'close':     float(row['close'])     if pd.notna(row.get('close'))     else None,
                    'adj_close': float(row['adj_close']) if pd.notna(row.get('adj_close')) else None,
                    'volume':    int(row['volume'])      if pd.notna(row.get('volume'))    else None,
                })
                inserted += 1
        logger.info(f"✓ {ticker:<22} {inserted} rows")
        return inserted
    except Exception as e:
        logger.error(f"✗ {ticker}: {e}")
        return 0

total = 0
for ticker in TICKERS:
    total += backfill(ticker, SECTOR_MAP.get(ticker, 'Unknown'))

logger.info(f"\nTotal rows upserted: {total:,}")