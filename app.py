import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pytz

# 1. Page Setup
st.set_page_config(page_title="Nifty 50 Pro Terminal", layout="wide")

# Custom Professional CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Force Metrics to White & Bold */
    [data-testid="stMetricLabel"] {
        color: white !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
    }
    [data-testid="stMetricValue"] {
        color: white !important;
        font-weight: 900 !important;
    }
    
    /* Header Ribbon Styling */
    .section-header-container {
        background-color: #1e2130; 
        padding: 12px; 
        border-radius: 5px; 
        margin: 20px 0; 
        border-left: 5px solid #00ffcc;
    }
    .header-text {
        color: white; 
        font-weight: 900; 
        font-size: 1.4rem; 
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Sector Mapping
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

# 3. Define Tickers
nifty_50_tickers = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", 
    "INFY.NS", "ITC.NS", "SBIN.NS", "LICI.NS", "HINDUNILVR.NS",
    "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "ADANIENT.NS", "TATAMOTORS.NS", "NTPC.NS", "TITAN.NS", "KOTAKBANK.NS", 
    "HDFCLIFE.NS", "M&M.NS", "DRREDDY.NS", "ONGC.NS", "TRENT.NS", "POWERGRID.NS", 
    "ULTRACEMCO.NS", "SBILIFE.NS", "ADANIPORTS.NS", "GRASIM.NS", "MAXHEALTH.NS", 
    "JIOFIN.NS", "TATASTEEL.NS", "ASIANPAINT.NS", "EICHERMOT.NS", "HINDALCO.NS", 
    "COALINDIA.NS", "CIPLA.NS", "INDIGO.NS", "APOLLOHOSP.NS", "JSWSTEEL.NS", 
    "TATACONSUM.NS", "NESTLEIND.NS", "BEL.NS", "AXISBANK.NS", "WIPRO.NS", 
    "TECHM.NS", "ADANIPOWER.NS", "SHREECEM.NS"
]

# --- FETCH MAIN STOCK DATA ---
@st.cache_data(ttl=600)
def fetch_pro_data(ticker_list):
    all_data = []
    for ticker in ticker_list:
        try:
            symbol_clean = ticker.replace(".NS", "")
            stock = yf.Ticker(ticker)
            hist = stock.history(period="10d")
            if len(hist) < 5: continue
            
            ltp, prev_close = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
            ma5 = hist['Close'].tail(5).mean()
            signal = "BULLISH" if ltp > ma5 else "BEARISH"
            
            info = stock.info
            high_52w = info.get('fiftyTwoWeekHigh', ltp)
            low_52w = info.get('fiftyTwoWeekLow', ltp)
            dist_high = ((high_52w - ltp) / high_52w) * 100
            dist_low = ((ltp - low_52w) / low_52w) * 100
            
            all_data.append({
                "Symbol": symbol_clean,
                "Sector": REVERSE_MAP.get(symbol_clean, "Other"),
                "LTP (₹)": round(ltp, 2),
                "Change (₹)": round(ltp - prev_close, 2),
                "Today %": round(((ltp - prev_close) / prev_close) * 100, 2),
                "Signal": signal,
                "Near 52W High": round(dist_high, 2),
                "Near 52W Low": round(dist_low, 2),
                "Volume": hist['Volume'].iloc[-1],
                "Market Cap (Cr)": round(stock.info.get('marketCap', 0) / 10**7, 2)
            })
        except: continue
    return pd.DataFrame(all_data)

# --- HELPER FUNCTION: Historical Performance ---
@st.cache_data(ttl=600)
def fetch_historical_perf_fixed(symbol):
    """Returns 1W, 1M, 1Y % change for a given stock symbol."""
    try:
        ticker = yf.Ticker(symbol + ".NS")
        data = ticker.history(period="1y", interval="1d")
        if data.empty:
            return {"1W": 0, "1M": 0, "1Y": 0}

        curr = data['Close'].iloc[-1]

        prev_week = data['Close'].iloc[-5] if len(data) >= 5 else data['Close'].iloc[0]
        change_1w = (curr - prev_week) / prev_week * 100

        prev_month = data['Close'].iloc[-21] if len(data) >= 21 else data['Close'].iloc[0]
        change_1m = (curr - prev_month) / prev_month * 100

        prev_year = data['Close'].iloc[-252] if len(data) >= 252 else data['Close'].iloc[0]
        change_1y = (curr - prev_year) / prev_year * 100

        return {"1W": change_1w, "1M": change_1m, "1Y": change_1y}
    except:
        return {"1W": 0, "1M": 0, "1Y": 0}

# --- MAIN APP LAYOUT ---
st.markdown('<div class="section-header-container"><span class="header-text">🌍 Global Market Pulse</span></div>', unsafe_allow_html=True)
idx_cols = st.columns(3)
indices = {"NIFTY 50": "^NSEI", "SENSEX": "^BSESN", "BANK NIFTY": "^NSEBANK"}

for i, (name, t) in enumerate(indices.items()):
    idx_h = yf.Ticker(t).history(period="5d")
    if len(idx_h) >= 2:
        p, prev = idx_h['Close'].iloc[-1], idx_h['Close'].iloc[-2]
        idx_cols[i].metric(label=name, value=f"{p:,.2f}", delta=f"{p-prev:,.2f} ({(p-prev)/prev*100:.2f}%)")

st.divider()

with st.spinner("Synchronizing with Exchange..."):
    df = fetch_pro_data(nifty_50_tickers)

if df is not None and not df.empty:
    
    with st.sidebar:
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%H:%M:%S')
        st.markdown(f"### 🕒 Last Updated: `{current_time} IST` ")
        
        st.markdown("---")
        st.markdown("### 🚀 Top 5 Gainers")
        for _, row in df.nlargest(5, 'Today %').iterrows():
            st.success(f"**{row['Symbol']}**: +{row['Today %']}%")
        
        st.markdown("---")
        st.markdown("### 📉 Top 5 Losers")
        for _, row in df.nsmallest(5, 'Today %').iterrows():
            st.error(f"**{row['Symbol']}**: {row['Today %']}%")
        
        if st.button("🔄 Full Refresh"):
            st.cache_data.clear()
            st.rerun()

    st.markdown('<div class="section-header-container"><span class="header-text">🏹 Market Sentiment & Breath</span></div>', unsafe_allow_html=True)
    adv, dec = len(df[df['Today %'] > 0]), len(df[df['Today %'] < 0])
    sent_pct = (adv / len(df)) * 100
    
    col_g1, col_g2 = st.columns([1, 2])
    with col_g1:
        st.metric("Advancers", adv, f"{adv} Stocks")
        st.metric("Decliners", dec, f"-{dec} Stocks", delta_color="inverse")
    
    with col_g2:
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = sent_pct,
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#00ffcc"}, 'bgcolor': "#1e2130",
                     'steps': [{'range': [0, 40], 'color': '#ff4b4b'}, {'range': [60, 100], 'color': '#00ffcc'}]}))
        fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=280, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown('<div class="section-header-container"><span class="header-text">📊 Nifty 50 Performance Matrix</span></div>', unsafe_allow_html=True)
    df['Trend'] = df['Today %'].apply(lambda x: "▲" if x >= 0 else "▼")
    
    df_display = df[['Symbol', 'Trend', 'Signal', 'Near 52W High', 'Near 52W Low', 'Sector', 'LTP (₹)', 'Change (₹)', 'Today %', 'Volume', 'Market Cap (Cr)']].sort_values("Today %", ascending=False)

    # --- FIXED Styler ---
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
        use_container_width=True, height=600, hide_index=True
    )

# --- HISTORICAL + VOLATILITY SIDE-BY-SIDE WITH COLOR ---
st.markdown('<div class="section-header-container"><span class="header-text">📜 Historical & Volatility Dashboard</span></div>', unsafe_allow_html=True)
col_hist, col_vol = st.columns(2)

# --- Left Column: Historical Comparisons ---
with col_hist:
    st.subheader("📜 Historical Comparisons")
    hist_results = [fetch_historical_perf_fixed(ticker) for ticker in df["Symbol"]]
    df_hist = pd.DataFrame(hist_results, index=df["Symbol"]).fillna(0)
    st.dataframe(
        df_hist.style.apply(
            lambda s: ['color: #00ff00; font-weight: bold;' if v>0 else 'color: #ff4b4b; font-weight: bold;' if v<0 else 'color: white; font-weight: bold;' for v in s]
        ).format({
            "1W": "{:+.2f}%", "1M": "{:+.2f}%", "1Y": "{:+.2f}%"
        }),
        use_container_width=True
    )

# --- Right Column: Volatility Dashboard ---
with col_vol:
    st.subheader("📊 Volatility Dashboard")
    vol_data = []
    for ticker in df["Symbol"]:
        try:
            hist = yf.Ticker(ticker+".NS").history(period="1mo")
            hist["returns"] = hist["Close"].pct_change()
            volatility = hist["returns"].std() * 100
            vol_data.append({"Symbol": ticker, "Volatility %": volatility})
        except:
            vol_data.append({"Symbol": ticker, "Volatility %": 0})

    vol_df = pd.DataFrame(vol_data).sort_values("Volatility %", ascending=False)

    st.dataframe(
        vol_df.style.apply(
            lambda s: ['color: #ff4b4b; font-weight: bold;' if v>4 else 'color: #ffcc00; font-weight: bold;' if v>2 else 'color: #00ff00; font-weight: bold;' for v in s],
            subset=['Volatility %']
        ).format({"Volatility %": "{:.2f}%"}),
        use_container_width=True
    )
