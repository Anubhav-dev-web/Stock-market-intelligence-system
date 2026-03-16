# pipelines/compute_indicators.py
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os, logging

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

def compute_and_load():
    logger.info("Loading raw prices...")
    df = pd.read_sql("""
        SELECT mp.ticker, mp.sector, mp.date,
               mp.open, mp.high, mp.low, mp.close, mp.volume,
               dc.company_key
        FROM raw.market_prices mp
        LEFT JOIN analytics.dim_companies dc USING(ticker)
        ORDER BY mp.ticker, mp.date
    """, engine)

    logger.info(f"Loaded {len(df):,} rows for {df['ticker'].nunique()} tickers")
    results = []

    for ticker, grp in df.groupby('ticker'):
        grp = grp.sort_values('date').copy()
        company_key = grp['company_key'].iloc[0]

        # Returns
        grp['daily_return_pct']   = grp['close'].pct_change() * 100
        grp['weekly_return_pct']  = grp['close'].pct_change(5) * 100
        grp['monthly_return_pct'] = grp['close'].pct_change(21) * 100

        # Moving averages
        grp['ma_20']  = grp['close'].rolling(20).mean()
        grp['ma_50']  = grp['close'].rolling(50).mean()
        grp['ma_200'] = grp['close'].rolling(200).mean()

        # Bollinger Bands
        grp['bb_mid']   = grp['close'].rolling(20).mean()
        grp['bb_std']   = grp['close'].rolling(20).std()
        grp['bb_upper'] = grp['bb_mid'] + 2 * grp['bb_std']
        grp['bb_lower'] = grp['bb_mid'] - 2 * grp['bb_std']

        # RSI-14
        delta    = grp['close'].diff()
        gain     = delta.clip(lower=0).rolling(14).mean()
        loss     = (-delta.clip(upper=0)).rolling(14).mean()
        rs       = gain / loss.replace(0, 1e-10)
        grp['rsi_14'] = 100 - (100 / (1 + rs))

        # 52-week high/low (252 trading days)
        grp['high_52w'] = grp['high'].rolling(252, min_periods=1).max()
        grp['low_52w']  = grp['low'].rolling(252, min_periods=1).min()
        grp['pct_from_52w_high'] = (
            (grp['close'] - grp['high_52w']) / grp['high_52w'] * 100
        )

        # Trend signal
        def trend(row):
            try:
                if row['close'] > row['ma_20'] > row['ma_50'] > row['ma_200']:
                    return 'Strong Bullish'
                elif row['close'] > row['ma_20'] > row['ma_50']:
                    return 'Bullish'
                elif row['close'] < row['ma_20'] < row['ma_50'] < row['ma_200']:
                    return 'Strong Bearish'
                elif row['close'] < row['ma_20'] < row['ma_50']:
                    return 'Bearish'
                return 'Neutral'
            except:
                return 'Neutral'

        grp['trend_signal'] = grp.apply(trend, axis=1)
        grp['rsi_zone'] = grp['rsi_14'].apply(
            lambda x: 'Overbought' if x >= 70 else ('Oversold' if x <= 30 else 'Neutral')
            if pd.notna(x) else 'Neutral'
        )
        grp['date_key']     = grp['date'].apply(
            lambda d: int(d.strftime('%Y%m%d'))
        )
        grp['company_key']  = company_key

        results.append(grp)
        logger.info(f"  ✓ {ticker:<22} indicators computed")

    final = pd.concat(results)

    cols = [
        'ticker','date_key','company_key',
        'open','high','low','close','volume',
        'daily_return_pct','weekly_return_pct','monthly_return_pct',
        'ma_20','ma_50','ma_200',
        'bb_upper','bb_lower','rsi_14',
        'high_52w','low_52w','pct_from_52w_high',
        'trend_signal','rsi_zone'
    ]
    final = final[cols].rename(columns={
        'open':'open_price','high':'high_price',
        'low':'low_price','close':'close_price'
    })

    logger.info(f"Loading {len(final):,} rows into analytics.fct_daily_prices...")
    final.to_sql('fct_daily_prices', engine, schema='analytics',
                 if_exists='append', index=False,
                 method='multi', chunksize=1000)

    logger.info("Done!")

if __name__ == '__main__':
    compute_and_load()