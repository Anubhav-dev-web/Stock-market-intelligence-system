# pipelines/daily_refresh.py
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, date
from dotenv import load_dotenv
import os, logging, time

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

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

ALL_TICKERS = list(SECTOR_MAP.keys())

def refresh_ticker(ticker: str) -> int:
    try:
        t  = yf.Ticker(ticker)
        df = t.history(period='5d', auto_adjust=False)
        if df is None or df.empty:
            return 0

        df.reset_index(inplace=True)
        df.columns    = [c.lower().replace(' ','_') for c in df.columns]
        df['date']    = pd.to_datetime(df['date']).dt.date
        df['ticker']  = ticker
        df['sector']  = SECTOR_MAP.get(ticker, 'Unknown')
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
                        open      = EXCLUDED.open,
                        high      = EXCLUDED.high,
                        low       = EXCLUDED.low,
                        close     = EXCLUDED.close,
                        adj_close = EXCLUDED.adj_close,
                        volume    = EXCLUDED.volume
                """), {
                    'ticker':    ticker,
                    'sector':    SECTOR_MAP.get(ticker, 'Unknown'),
                    'date':      row['date'],
                    'open':      float(row['open'])      if pd.notna(row.get('open'))      else None,
                    'high':      float(row['high'])      if pd.notna(row.get('high'))      else None,
                    'low':       float(row['low'])       if pd.notna(row.get('low'))       else None,
                    'close':     float(row['close'])     if pd.notna(row.get('close'))     else None,
                    'adj_close': float(row['adj_close']) if pd.notna(row.get('adj_close')) else None,
                    'volume':    int(row['volume'])      if pd.notna(row.get('volume'))    else None,
                })
                inserted += 1
        return inserted

    except Exception as e:
        logger.error(f"  ✗ {ticker}: {e}")
        return 0


def run_daily_refresh():
    logger.info(f"Daily refresh — {date.today()}")
    logger.info("=" * 50)
    total = 0
    for ticker in ALL_TICKERS:
        rows = refresh_ticker(ticker)
        if rows > 0:
            logger.info(f"  ✓ {ticker:<22} {rows} rows upserted")
        time.sleep(0.3)
        total += rows
    logger.info(f"Refresh complete — {total} rows upserted")


if __name__ == '__main__':
    run_daily_refresh()