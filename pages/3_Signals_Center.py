import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from services.earnings_service import get_all_earnings, load_tickers_from_db, seed_default_tickers
from services.signal_service import evaluate_signals, get_active_signals, save_signals_to_db
from services.telegram_service import send_signal_alert
from database.models import init_db, get_session, Signal
from config.settings import DB_PATH, BUY_SIGNAL_DAYS, SELL_SIGNAL_DAYS

st.set_page_config(page_title="Signals Center", page_icon="🎯", layout="wide")
st.title("🎯 Signals Center")

init_db(DB_PATH)
seed_default_tickers()

@st.cache_data(ttl=1800)
def load_signals():
    tickers = load_tickers_from_db()
    df = get_all_earnings(tickers)
    if not df.empty:
        df = evaluate_signals(df)
        save_signals_to_db(df)
    return df

df = load_signals()

# Signal Rules info
with st.expander("📖 Signal Rules", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"🟢 **BUY SIGNAL** = E-{BUY_SIGNAL_DAYS} (10 trading days before earnings)")
    with col2:
        st.error(f"🔴 **SELL SIGNAL** = E-{SELL_SIGNAL_DAYS} (2 trading days before earnings)")

if df.empty or "signal" not in df.columns:
    st.warning("No signals available. Fetch earnings data first.")
    st.stop()

# Active signals
buy_df = df[df["signal"] == "BUY"]
sell_df = df[df["signal"] == "SELL"]
watch_df = df[df["signal"] == "WATCH"]

tab1, tab2, tab3, tab4 = st.tabs(["🟢 BUY Signals", "🔴 SELL Signals", "🟡 WATCH List", "📜 Signal History"])

def format_signal_df(sdf):
    if sdf.empty:
        return sdf
    cols = [c for c in ["symbol", "name", "earnings_date", "trading_days", "sector", "timing"] if c in sdf.columns]
    out = sdf[cols].copy()
    if "earnings_date" in out.columns:
        out["earnings_date"] = pd.to_datetime(out["earnings_date"]).dt.strftime("%Y-%m-%d")
    return out

with tab1:
    st.markdown(f"### 🟢 Active BUY Signals ({len(buy_df)})")
    if buy_df.empty:
        st.info("No active BUY signals at this time.")
    else:
        st.dataframe(format_signal_df(buy_df), use_container_width=True)
        if st.button("📤 Send BUY Alerts via Telegram", type="primary"):
            for _, row in buy_df.iterrows():
                result = send_signal_alert(row["symbol"], "BUY", row.get("earnings_date"), row.get("trading_days", 0), 0.0)
                if result:
                    st.success(f"Sent alert for {row['symbol']}")
                else:
                    st.error(f"Failed to send alert for {row['symbol']} — check Telegram config")

with tab2:
    st.markdown(f"### 🔴 Active SELL Signals ({len(sell_df)})")
    if sell_df.empty:
        st.info("No active SELL signals at this time.")
    else:
        st.dataframe(format_signal_df(sell_df), use_container_width=True)
        if st.button("📤 Send SELL Alerts via Telegram", type="primary"):
            for _, row in sell_df.iterrows():
                result = send_signal_alert(row["symbol"], "SELL", row.get("earnings_date"), row.get("trading_days", 0), 0.0)
                if result:
                    st.success(f"Sent alert for {row['symbol']}")

with tab3:
    st.markdown(f"### 🟡 WATCH List ({len(watch_df)})")
    st.caption(f"Tickers within the next {BUY_SIGNAL_DAYS}+ trading days")
    if watch_df.empty:
        st.info("No tickers on watch list.")
    else:
        st.dataframe(format_signal_df(watch_df), use_container_width=True)

with tab4:
    st.markdown("### 📜 Signal History from Database")
    hist = get_active_signals()
    if hist.empty:
        st.info("No historical signals in database yet.")
    else:
        if "signal_date" in hist.columns:
            hist["signal_date"] = pd.to_datetime(hist["signal_date"]).dt.strftime("%Y-%m-%d %H:%M")
        if "earnings_date" in hist.columns:
            hist["earnings_date"] = pd.to_datetime(hist["earnings_date"]).dt.strftime("%Y-%m-%d")
        st.dataframe(hist, use_container_width=True)
