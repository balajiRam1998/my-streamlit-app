import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pytz

# 1. Page Setup
st.set_page_config(page_title="Nifty 50 Pro Terminal", layout="wide")

# --- CSS Styles for Single-Screen Fit ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; font-family: monospace; overflow: hidden; }

    /* Header Ribbon */
    .section-header-container {
        background-color: #1e2130; 
        padding: 4px 8px; 
        border-radius: 4px; 
        margin: 2px 0 5px 0; 
        border-left: 3px solid #00ffcc;
    }
    .header-text { color: white; font-weight: 900; font-size: 1rem; letter-spacing: 1px; text-transform: uppercase; }

    /* Metrics Font */
    div[data-testid="metric-container"] > div:nth-child(1) { font-size: 0.6rem !important; color: white; font-weight: 600; }
    div[data-testid="metric-container"] > div:nth-child(2) { font-size: 0.8rem !important; color: white; font-weight: 700; }
    div[data-testid="metric-container"] > div:nth-child(3) { font-size: 0.6rem !important; color: white; }

    /* Last Updated Small */
    .last-updated-small { font-size: 7px !important; font-weight: 600; color: #00ffcc; margin-bottom: 3px; }

    /* Gainers/Losers List */
    .small-list-item { font-size: 10px !important; font-weight: 600; color: #ffffff; display: block; margin-bottom: 2px; }

    /* Dataframe compact */
    .dataframe tbody tr td, .dataframe thead tr th { color: white !important; font-size: 0.6rem !important; padding: 2px 4px; }

    /* Reduce chart padding */
    .stPlotlyChart div { padding:0px !important; }
    </style>
""", unsafe_allow_html=True)

# --- Sector Mapping ---
SECTOR_MAP = {
    "Banking/Finance": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "BAJFINANCE", "JIOFIN", "HDFCLIFE", "SBILIFE"],
    "IT/Technology": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM"],
    "Energy/Oil": ["RELIANCE", "ONGC", "NTPC", "POWERGRID", "COALINDIA", "ADANIPOWER"],
    "Consumer Goods": ["ITC", "HINDUNILVR", "NESTLEIND", "TATACONSUM", "ASIANPAINT", "TITAN"],
    "Automobile": ["TATAMOTORS", "MARUTI", "M&M", "EICHERMOT"],
    "Pharma/Health": ["SUNPHARMA", "DRREDDY", "CIPLA", "MAXHEALTH", "APOLLOHOSP"],
    "Metals/Mining": ["TATASTEEL", "HINDALCO", "JSWSTEEL"],
    "Infrastructure/Misc": ["LT", "ADANIENT", "ADANIPORTS", "GRASIM", "ULTRACEMCO", "TRENT", "BEL", "SHREECEM", "INDIGO"]
}
REVERSE_MAP = {ticker: sector for sector, tickers in SECTOR_MAP.items() for ticker in tickers}

# --- Nifty 50 Tickers ---
nifty_50_tickers = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", 
    "INFY.NS", "ITC.NS", "SBIN.NS", "LICI.NS", "HINDUNILVR.NS",
    "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "ADANIENT.NS", "TMPV.NS", "NTPC.NS", "TITAN.NS", "KOTAKBANK.NS", 
    "HDFCLIFE.NS", "M&M.NS", "DRREDDY.NS", "ONGC.NS", "TRENT.NS", "POWERGRID.NS", 
    "ULTRACEMCO.NS", "SBILIFE.NS", "ADANIPORTS.NS", "GRASIM.NS", "MAXHEALTH.NS", 
    "JIOFIN.NS", "TATASTEEL.NS", "ASIANPAINT.NS", "EICHERMOT.NS", "HINDALCO.NS", 
    "COALINDIA.NS", "CIPLA.NS", "INDIGO.NS", "APOLLOHOSP.NS", "JSWSTEEL.NS", 
    "TATACONSUM.NS", "NESTLEIND.NS", "BEL.NS", "AXISBANK.NS", "WIPRO.NS", 
    "TECHM.NS", "ADANIPOWER.NS", "SHREECEM.NS"
]

# --- Fetch Stock Data ---
@st.cache_data(ttl=600)
def fetch_pro_data(ticker_list):
    all_data = []
    for ticker in ticker_list:
        try:
            symbol_clean = ticker.replace(".NS", "")
            stock = yf.Ticker(ticker)
            hist = stock.history(period="30d")
            if len(hist) < 21: continue
            ltp = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            close_20 = hist['Close'].iloc[-20]
            close_10 = hist['Close'].iloc[-10]
            if close_20 < ltp: signal = "BULLISH"
            elif close_10 > ltp: signal = "BEARISH"
            else: signal = "NEUTRAL"
            info = stock.info
            high_52w = info.get('fiftyTwoWeekHigh', ltp)
            low_52w = info.get('fiftyTwoWeekLow', ltp)
            dist_high = ((high_52w - ltp) / high_52w) * 100
            dist_low = ((ltp - low_52w) / low_52w) * 100
            all_data.append({
                "Symbol": symbol_clean,
                "Sector": REVERSE_MAP.get(symbol_clean, "Other"),
                "LTP (₹)": round(ltp,2),
                "Change (₹)": round(ltp-prev_close,2),
                "Today %": round(((ltp-prev_close)/prev_close)*100,2),
                "Signal": signal,
                "Near 52W High": round(dist_high,2),
                "Near 52W Low": round(dist_low,2),
                "Volume": hist['Volume'].iloc[-1],
                "Market Cap (Cr)": round(stock.info.get('marketCap',0)/10**7,2)
            })
        except: continue
    return pd.DataFrame(all_data)

# --- Historical Performance ---
@st.cache_data(ttl=600)
def fetch_historical_perf(symbol):
    try:
        ticker = yf.Ticker(symbol+".NS")
        data = ticker.history(period="1y", interval="1d")
        if data.empty: return {"1W":0,"1M":0,"1Y":0}
        curr = data['Close'].iloc[-1]
        prev_week = data['Close'].iloc[-5] if len(data)>=5 else data['Close'].iloc[0]
        prev_month = data['Close'].iloc[-21] if len(data)>=21 else data['Close'].iloc[0]
        prev_year = data['Close'].iloc[-252] if len(data)>=252 else data['Close'].iloc[0]
        return {"1W": (curr-prev_week)/prev_week*100, "1M": (curr-prev_month)/prev_month*100, "1Y": (curr-prev_year)/prev_year*100}
    except: return {"1W":0,"1M":0,"1Y":0}

# --- Fetch Data ---
with st.spinner("Fetching Nifty 50 Data..."):
    df = fetch_pro_data(nifty_50_tickers)

# --- TOP ROW: 3 Columns ---
top_cols = st.columns([1,1,1])

# --- Top Left: Indian Market Pulse ---
with top_cols[0]:
    st.markdown('<div class="section-header-container"><span class="header-text">🌍 Indian Market Pulse</span></div>', unsafe_allow_html=True)
    indices = {"NIFTY 50": "^NSEI", "SENSEX": "^BSESN", "BANK NIFTY": "^NSEBANK"}
    idx_cols = st.columns(3)
    for i, (name, t) in enumerate(indices.items()):
        idx_h = yf.Ticker(t).history(period="5d")
        if len(idx_h) >= 2:
            p, prev = idx_h['Close'].iloc[-1], idx_h['Close'].iloc[-2]
            idx_cols[i].metric(label=name, value=f"{p:,.2f}", delta=f"{p-prev:,.2f} ({(p-prev)/prev*100:.2f}%)")

# --- Top Middle: Market Sentiment ---
with top_cols[1]:
    st.markdown('<div class="section-header-container"><span class="header-text">🏹 Market Sentiment</span></div>', unsafe_allow_html=True)
    adv, dec = len(df[df['Today %']>0]), len(df[df['Today %']<0])
    sent_pct = (adv/len(df))*100
    ms_cols = st.columns(2)
    ms_cols[0].metric("Advancers", adv, f"{adv} Stocks")
    ms_cols[1].metric("Decliners", dec, f"{dec} Stocks", delta_color="inverse")
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=sent_pct,
        gauge={'axis':{'range':[0,100]}, 'bar':{'color':'#00ffcc'}, 'bgcolor':'#1e2130',
               'steps':[{'range':[0,40],'color':'#ff4b4b'},{'range':[60,100],'color':'#00ffcc'}]}))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color':"white"}, height=150, margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig_gauge,use_container_width=True)

# --- Top Right: Top Gainers / Losers ---
with top_cols[2]:
    st.markdown('<div class="section-header-container"><span class="header-text">🚀 Top Gainers / 📉 Top Losers</span></div>', unsafe_allow_html=True)
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%H:%M:%S')
    st.markdown(f"<div class='last-updated-small'>🕒 Last Updated: {current_time} IST</div>", unsafe_allow_html=True)
    tl_cols = st.columns(2)
    with tl_cols[0]:
        st.markdown("### 🚀 Top 5 Gainers")
        for _, row in df.nlargest(5,'Today %').iterrows():
            st.markdown(f"<span class='small-list-item'>🚀 {row['Symbol']}: +{row['Today %']}%</span>", unsafe_allow_html=True)
    with tl_cols[1]:
        st.markdown("### 📉 Top 5 Losers")
        for _, row in df.nsmallest(5,'Today %').iterrows():
            st.markdown(f"<span class='small-list-item'>📉 {row['Symbol']}: {row['Today %']}%</span>", unsafe_allow_html=True)

# --- BOTTOM ROW: 3 Columns ---
bottom_cols = st.columns([1,1,1])

# --- Bottom Left: Performance Matrix ---
with bottom_cols[0]:
    st.markdown('<div class="section-header-container"><span class="header-text">📊 Nifty 50 Matrix</span></div>', unsafe_allow_html=True)
    df['Trend'] = df['Today %'].apply(lambda x: "▲" if x>=0 else "▼")
    df_display = df[['Symbol','Trend','Signal','Near 52W High','Near 52W Low','Sector','LTP (₹)','Change (₹)','Today %','Volume','Market Cap (Cr)']].sort_values("Today %",ascending=False)
    st.dataframe(
        df_display.style
        .apply(
            lambda s: ['color: #00ff15b8; font-weight: bold;' if v=='BULLISH' else 'color: #ff4b4b; font-weight: bold;' for v in s], 
            subset=['Signal']
        )
        .format({
            "LTP (₹)": "{:,.2f}", 
            "Change (₹)": "{:+.2f}", 
            "Today %": "{:+.2f}%", 
            "Near 52W High": "{:.2f}%", 
            "Near 52W Low": "{:.2f}%", 
            "Volume": "{:,}", 
            "Market Cap (Cr)": "{:,.0f}"
        }),
        use_container_width=True, height=300,
    )
# --- Bottom Middle: Historical Comparisons ---
with bottom_cols[1]:
    st.markdown('<div class="section-header-container"><span class="header-text">📜 Historical</span></div>', unsafe_allow_html=True)
    hist_results = [fetch_historical_perf(ticker) for ticker in df["Symbol"]]
    df_hist = pd.DataFrame(hist_results,index=df["Symbol"]).fillna(0)
    st.dataframe(
        df_hist.style.apply(
            lambda s: ['color: #00ff00; font-weight: bold;' if v>0 else 'color: #ff4b4b; font-weight: bold;' if v<0 else 'color: white; font-weight: bold;' for v in s]
        ).format({
            "1W": "{:+.2f}%", "1M": "{:+.2f}%", "1Y": "{:+.2f}%"
        }),
        use_container_width=True, height=300
    )
# --- Bottom Right: Volatility Dashboard ---
with bottom_cols[2]:
    st.markdown('<div class="section-header-container"><span class="header-text">📊 Volatility</span></div>', unsafe_allow_html=True)
    vol_data=[]
    for ticker in df["Symbol"]:
        try:
            hist = yf.Ticker(ticker+".NS").history(period="1mo")
            hist["returns"]=hist["Close"].pct_change()
            volatility = hist["returns"].std()*100
            vol_data.append({"Symbol":ticker,"Volatility %":volatility})
        except:
            vol_data.append({"Symbol":ticker,"Volatility %":0})
    vol_df=pd.DataFrame(vol_data).sort_values("Volatility %",ascending=False)

    st.dataframe(
        vol_df.style.apply(
            lambda s: ['color: #ff4b4b; font-weight: bold;' if v>4 else 'color: #ffcc00; font-weight: bold;' if v>2 else 'color: #00ff00; font-weight: bold;' for v in s],
            subset=['Volatility %']
        ).format({"Volatility %": "{:.2f}%"}),
        use_container_width=True, height=300
    )
