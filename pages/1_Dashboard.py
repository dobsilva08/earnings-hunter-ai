import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from services.earnings_service import get_all_earnings, load_tickers_from_db, seed_default_tickers
from services.signal_service import evaluate_signals, get_signal_color, save_signals_to_db
from services.telegram_service import send_signal_alert
from database.models import init_db
from config.settings import DB_PATH

st.set_page_config(page_title="Dashboard - Earnings Hunter AI", page_icon="📊", layout="wide")

st.markdown("""
<style>
.buy-badge { background:#003300; color:#00FF41; border:1px solid #00FF41; padding:3px 10px; border-radius:3px; font-weight:bold; }
.sell-badge { background:#330000; color:#FF4444; border:1px solid #FF4444; padding:3px 10px; border-radius:3px; font-weight:bold; }
.watch-badge { background:#332200; color:#FFD700; border:1px solid #FFD700; padding:3px 10px; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Earnings Dashboard")

init_db(DB_PATH)
seed_default_tickers()

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Controls")
    auto_refresh = st.toggle("Auto Refresh", value=False)
    if st.button("🔄 Fetch Earnings Now", use_container_width=True, type="primary"):
        st.session_state["refresh"] = True
    st.divider()
    st.caption(f"Last update: {datetime.now().strftime('%H:%M:%S')}")

# Load data
@st.cache_data(ttl=3600, show_spinner="Fetching earnings data...")
def load_data():
    tickers = load_tickers_from_db()
    df = get_all_earnings(tickers)
    if not df.empty:
        df = evaluate_signals(df)
        save_signals_to_db(df)
    return df

if st.session_state.get("refresh", False):
    st.cache_data.clear()
    st.session_state["refresh"] = False

with st.spinner("Loading earnings data..."):
    df = load_data()

if df.empty:
    st.warning("No earnings data found. Click Fetch Earnings Now to load data.")
    st.stop()

# KPI Cards
st.markdown("### 📌 Market Overview")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
buy_count = len(df[df["signal"] == "BUY"]) if "signal" in df.columns else 0
sell_count = len(df[df["signal"] == "SELL"]) if "signal" in df.columns else 0
watch_count = len(df[df["signal"] == "WATCH"]) if "signal" in df.columns else 0
total = len(df)

with kpi1:
    st.metric("Total Tracked", total, delta=None)
with kpi2:
    st.metric("🟢 BUY Signals", buy_count)
with kpi3:
    st.metric("🔴 SELL Signals", sell_count)
with kpi4:
    st.metric("🟡 WATCH", watch_count)
with kpi5:
    next_earnings = df[df["earnings_date"] >= pd.Timestamp.now()]
    if not next_earnings.empty:
        next_sym = next_earnings.iloc[0]["symbol"]
        next_days = next_earnings.iloc[0].get("trading_days", "?")
        st.metric("Next Earnings", next_sym, delta=f"E-{next_days} days")
    else:
        st.metric("Next Earnings", "N/A")

st.divider()

# Main Table
st.markdown("### 📋 Earnings Tracker")
filter_signal = st.multiselect("Filter by Signal", ["BUY", "SELL", "WATCH", "PASSED"], default=["BUY", "SELL", "WATCH"])
if filter_signal and "signal" in df.columns:
    display_df = df[df["signal"].isin(filter_signal)].copy()
else:
    display_df = df.copy()

if "earnings_date" in display_df.columns:
    display_df["earnings_date"] = pd.to_datetime(display_df["earnings_date"]).dt.strftime("%Y-%m-%d")

def color_signal(val):
    colors = {"BUY": "color: #00FF41; font-weight: bold", "SELL": "color: #FF4444; font-weight: bold",
              "WATCH": "color: #FFD700", "PASSED": "color: #666666"}
    return colors.get(val, "")

cols_to_show = [c for c in ["symbol", "name", "earnings_date", "trading_days", "signal", "sector", "timing"] if c in display_df.columns]
styled = display_df[cols_to_show].style.applymap(color_signal, subset=["signal"] if "signal" in cols_to_show else [])
st.dataframe(styled, use_container_width=True, height=400)

# Charts row
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📅 Earnings Timeline")
    if "trading_days" in df.columns and not df.empty:
        timeline_df = df[df["trading_days"] >= 0].sort_values("trading_days").head(20)
        if not timeline_df.empty:
            fig = go.Figure()
            signal_colors = {"BUY": "#00FF41", "SELL": "#FF4444", "WATCH": "#FFD700", "PASSED": "#666"}
            for sig in ["BUY", "SELL", "WATCH"]:
                mask = timeline_df["signal"] == sig if "signal" in timeline_df.columns else pd.Series([False]*len(timeline_df))
                sub = timeline_df[mask]
                if not sub.empty:
                    fig.add_trace(go.Bar(
                        x=sub["symbol"], y=sub["trading_days"],
                        name=sig, marker_color=signal_colors[sig],
                        text=sub["trading_days"], textposition="outside"
                    ))
            fig.update_layout(paper_bgcolor="#0D0D0D", plot_bgcolor="#0D0D0D",
                              font_color="#E0E0E0", title="Trading Days to Earnings",
                              xaxis_tickangle=-45, showlegend=True, height=350)
            st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🎯 Signal Distribution")
    if "signal" in df.columns:
        sig_counts = df["signal"].value_counts()
        fig2 = go.Figure(data=[go.Pie(
            labels=sig_counts.index,
            values=sig_counts.values,
            marker_colors=["#00FF41", "#FF4444", "#FFD700", "#666666"],
            hole=0.4
        )])
        fig2.update_layout(paper_bgcolor="#0D0D0D", font_color="#E0E0E0",
                           title="Signal Distribution", height=350)
        st.plotly_chart(fig2, use_container_width=True)
