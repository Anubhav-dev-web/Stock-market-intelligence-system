import google.generativeai as genai
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
GEMINI_TIMEOUT_SECONDS = int(os.getenv('GEMINI_TIMEOUT_SECONDS', '30'))

genai.configure(api_key=GEMINI_API_KEY)

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

def get_market_snapshot():
    with engine.connect() as conn:

        latest_date = conn.execute(text("""
            SELECT MAX(date_key) 
            FROM analytics.fct_daily_prices 
            WHERE daily_return_pct IS NOT NULL
        """)).scalar()

        sectors = conn.execute(text("""
            SELECT sector, 
                   ROUND(AVG(daily_return_pct)::NUMERIC, 2)   AS avg_1d,
                   ROUND(AVG(weekly_return_pct)::NUMERIC, 2)  AS avg_1w,
                   ROUND(AVG(monthly_return_pct)::NUMERIC, 2) AS avg_1m
            FROM analytics.fct_daily_prices f
            JOIN analytics.dim_companies d USING(ticker)
            WHERE f.date_key = :dt
            AND d.is_index     = false
            AND d.is_commodity = false
            GROUP BY sector
            ORDER BY avg_1d DESC
        """), {'dt': latest_date}).fetchall()

        top_movers = conn.execute(text("""
            SELECT dc.company_name, dc.sector,
                   ROUND(f.daily_return_pct::NUMERIC, 2)  AS ret,
                   ROUND(f.rsi_14::NUMERIC, 1)            AS rsi,
                   f.trend_signal
            FROM analytics.fct_daily_prices f
            JOIN analytics.dim_companies dc USING(ticker)
            WHERE f.date_key = :dt
            AND dc.is_index     = false
            AND dc.is_commodity = false
            AND f.daily_return_pct IS NOT NULL
            ORDER BY ABS(f.daily_return_pct) DESC
            LIMIT 5
        """), {'dt': latest_date}).fetchall()

        nifty = conn.execute(text("""
            SELECT close_price, daily_return_pct
            FROM analytics.fct_daily_prices
            WHERE ticker = '^NSEI'
            ORDER BY date_key DESC
            LIMIT 1
        """)).fetchone()

        commodities = conn.execute(text("""
            SELECT ticker,
                   ROUND(price_inr::NUMERIC, 2)      AS price,
                   ROUND(inr_return_pct::NUMERIC, 2) AS change_pct
            FROM analytics.v_commodities_inr
            WHERE date = (
                SELECT MAX(date) FROM analytics.v_commodities_inr
            )
        """)).fetchall()

    return sectors, top_movers, nifty, commodities, latest_date


def generate_commentary():
    sectors, movers, nifty, commodities, latest_date = get_market_snapshot()

    sector_text = "\n".join([
        f"  {r[0]:<12} 1D: {r[1]:>6}%  1W: {r[2]:>6}%  1M: {r[3]:>6}%"
        for r in sectors
    ])

    movers_text = "\n".join([
        f"  {r[0]} ({r[1]}): {r[2]:+.2f}% | RSI {r[3]} | {r[4]}"
        for r in movers
    ])

    commodity_text = "\n".join([
        f"  {r[0]}: ₹{r[1]:,.2f} ({r[2]:+.2f}%)"
        for r in commodities
    ])

    prompt = f"""You are a senior Indian equity market analyst writing a 
morning market briefing for institutional investors.

Date: {latest_date}

NIFTY 50: {nifty[0]:,.2f} ({nifty[1]:+.2f}%)

SECTOR PERFORMANCE:
{sector_text}

TOP MOVERS:
{movers_text}

COMMODITIES IN INR:
{commodity_text}

Write a professional 3-paragraph market commentary (max 150 words):
- Paragraph 1: Overall market tone and NIFTY direction
- Paragraph 2: Sector rotation and standout sectors  
- Paragraph 3: Key stock moves and brief outlook

Rules:
- Use specific numbers from the data
- Write for an Indian institutional investor audience
- Flowing prose only — no bullet points
- Mention rupee impact on commodities where relevant
- Keep it concise and data-driven"""

    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(
        prompt,
        request_options={'timeout': GEMINI_TIMEOUT_SECONDS},
    )
    return response.text


def save_commentary(commentary: str):
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS analytics.ai_commentary (
                id            SERIAL PRIMARY KEY,
                commentary    TEXT,
                generated_at  TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            INSERT INTO analytics.ai_commentary (commentary)
            VALUES (:commentary)
        """), {'commentary': commentary})
    print("✓ Commentary saved to database")


if __name__ == '__main__':
    print("Fetching market data from PostgreSQL...")
    commentary = generate_commentary()
    print("\n── AI Market Commentary ──\n")
    print(commentary)
    print("\n" + "─" * 50)
    save_commentary(commentary)
    print("✓ Saved to analytics.ai_commentary table")
