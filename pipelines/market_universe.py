UNIVERSE = {
    "IT": [
        "TCS.NS",
        "INFY.NS",
        "WIPRO.NS",
        "HCLTECH.NS",
        "TECHM.NS",
        "LTIM.NS",
        "MPHASIS.NS",
        "PERSISTENT.NS",
        "COFORGE.NS",
        "OFSS.NS",
    ],
    "Banking": [
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "KOTAKBANK.NS",
        "SBIN.NS",
        "AXISBANK.NS",
        "BAJFINANCE.NS",
        "BAJAJFINSV.NS",
        "INDUSINDBK.NS",
        "PNB.NS",
        "HDFCLIFE.NS",
    ],
    "Pharma": [
        "SUNPHARMA.NS",
        "DRREDDY.NS",
        "CIPLA.NS",
        "DIVISLAB.NS",
        "APOLLOHOSP.NS",
        "TORNTPHARM.NS",
        "AUROPHARMA.NS",
        "LUPIN.NS",
        "BIOCON.NS",
        "MAXHEALTH.NS",
    ],
    "Energy": [
        "RELIANCE.NS",
        "ONGC.NS",
        "NTPC.NS",
        "POWERGRID.NS",
        "IOC.NS",
        "ADANIGREEN.NS",
        "TATAPOWER.NS",
        "COALINDIA.NS",
        "BPCL.NS",
        "ADANIPORTS.NS",
    ],
    "FMCG": [
        "HINDUNILVR.NS",
        "ITC.NS",
        "NESTLEIND.NS",
        "BRITANNIA.NS",
        "DABUR.NS",
        "MARICO.NS",
        "GODREJCP.NS",
        "COLPAL.NS",
        "EMAMILTD.NS",
        "TATACONSUM.NS",
    ],
    "Commodity": ["GC=F", "CL=F", "SI=F"],
    "Index": ["^NSEI", "^BSESN", "^NSEBANK", "^CNXIT", "^INDIAVIX", "USDINR=X"],
}

SECTOR_MAP = {
    ticker: sector
    for sector, tickers in UNIVERSE.items()
    for ticker in tickers
}

ALL_TICKERS = list(SECTOR_MAP)
