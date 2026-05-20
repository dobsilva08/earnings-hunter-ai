import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
from services.earnings_service import load_tickers_from_db, seed_default_tickers
from services.signal_service import get_active_signals
from database.models import init_db
from config.settings import DB_PATH

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")
st.title("📈 Analytics & Performance")

init_db(DB_PATH)
seed_default_tickers()

tab1, tab2, tab3 = st.tabs(["📊 Price Charts", "📉 Pre-Earnings Analysis", "🏆 Signal History"])

with tab1:
    st.markdown("### 📊 Stock Price Chart")
    tickers = load_tickers_from_db()
    selected = st.selectbox("Select Ticker", tickers)
    period = st.select_slider("Period", ["1mo", "3mo", "6mo", "1y", "2y"], value="3mo")
    
    if selected:
        with st.spinner(f"Loading {selected}..."):
            try:
                ticker = yf.Ticker(selected)
                hist = ticker.history(period=period)
                info = ticker.info
                
                if not hist.empty:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        price = hist["Close"].iloc[-1]
                        prev = hist["Close"].iloc[-2] if len(hist) > 1 else price
                        st.metric("Current Price", f"${price:.2f}", f"{((price/prev)-1)*100:.2f}%")
                    with col2:
                        st.metric("52W High", f"${hist['High'].max():.2f}")
                    with col3:
                        st.metric("52W Low", f"${hist['Low'].min():.2f}")
                    
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=hist.index,
                        open=hist["Open"], high=hist["High"],
                        low=hist["Low"], close=hist["Close"],
                        name=selected,
                        increasing_line_color="#00FF41",
                        decreasing_line_color="#FF4444"
                    ))
                    fig.add_trace(go.Bar(
                        x=hist.index, y=hist["Volume"],
                        name="Volume", yaxis="y2",
                        marker_color="rgba(0,255,65,0.2)"
                    ))
                    fig.update_layout(
                        paper_bgcolor="#0D0D0D", plot_bgcolor="#0D0D0D",
                        font_color="#E0E0E0", title=f"{selected} Price Chart",
                        yaxis2=dict(overlaying="y", side="right"),
                        height=500, xaxis_rangeslider_visible=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No price data available.")
            except Exception as e:
                st.error(f"Error loading data: {e}")

with tab2:
    st.markdown("### 📉 Pre-Earnings Price Pattern")
    st.info("Analyzes average price movement in the 10 trading days before earnings")
    selected2 = st.selectbox("Select Ticker for Analysis", load_tickers_from_db(), key="analytics2")
    
    if selected2 and st.button("Run Analysis", type="primary"):
        with st.spinner("Analyzing historical patterns..."):
            try:
                ticker2 = yf.Ticker(selected2)
                hist2 = ticker2.history(period="2y")
                if not hist2.empty:
                    returns = hist2["Close"].pct_change().dropna()
                    st.metric("Avg Daily Return", f"{returns.mean()*100:.3f}%")
                    st.metric("Volatility (std)", f"{returns.std()*100:.3f}%")
                    
                    fig3 = px.histogram(returns*100, nbins=50, title=f"{selected2} Return Distribution")
                    fig3.update_layout(paper_bgcolor="#0D0D0D", plot_bgcolor="#0D0D0D",
                                       font_color="#E0E0E0", xaxis_title="Daily Return (%)")
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.warning("Insufficient data.")
            except Exception as e:
                st.error(f"Error: {e}")

with tab3:
    st.markdown("### 🏆 Signal Database Stats")
    signals = get_active_signals()
    if signals.empty:
        st.info("No signals in database yet.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Signals", len(signals))
        with col2:
            if "signal_type" in signals.columns:
                buys = len(signals[signals["signal_type"] == "BUY"])
                st.metric("BUY Signals", buys)
        with col3:
            if "signal_type" in signals.columns:
                sells = len(signals[signals["signal_type"] == "SELL"])
                st.metric("SELL Signals", sells)
        
        if "signal_type" in signals.columns:
            sig_counts = signals["signal_type"].value_counts()
            fig4 = px.bar(x=sig_counts.index, y=sig_counts.values,
                          color=sig_counts.index,
                          color_discrete_map={"BUY": "#00FF41", "SELL": "#FF4444"},
                          title="Signal Type Distribution")
            fig4.update_layout(paper_bgcolor="#0D0D0D", plot_bgcolor="#0D0D0D",
                               font_color="#E0E0E0")
            st.plotly_chart(fig4, use_container_width=True)
        
        if "signal_date" in signals.columns:
            signals["signal_date"] = pd.to_datetime(signals["signal_date"]).dt.strftime("%Y-%m-%d")
        if "earnings_date" in signals.columns:
            signals["earnings_date"] = pd.to_datetime(signals["earnings_date"]).dt.strftime("%Y-%m-%d")
        st.dataframe(signals, use_container_width=True)
