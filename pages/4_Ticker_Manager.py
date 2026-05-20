import streamlit as st
import pandas as pd
from services.earnings_service import add_ticker, remove_ticker, load_tickers_from_db, seed_default_tickers
from database.models import init_db, get_session, Ticker
from config.settings import DB_PATH

st.set_page_config(page_title="Ticker Manager", page_icon="➕", layout="wide")
st.title("➕ Ticker Manager")

init_db(DB_PATH)
seed_default_tickers()

# Add Ticker
st.markdown("### Add New Ticker")
col1, col2 = st.columns([3, 1])
with col1:
    new_ticker = st.text_input("Enter ticker symbol (e.g., AAPL, MSFT)", placeholder="TICKER").upper().strip()
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Add Ticker", type="primary", use_container_width=True):
        if new_ticker:
            with st.spinner(f"Adding {new_ticker}..."):
                success = add_ticker(new_ticker)
            if success:
                st.success(f"✅ {new_ticker} added successfully!")
                st.cache_data.clear()
            else:
                st.error(f"❌ Failed to add {new_ticker}. Check if it is a valid symbol.")
        else:
            st.warning("Please enter a ticker symbol.")

st.divider()

# Current Tickers
st.markdown("### 📋 Active Tickers")
try:
    session = get_session(DB_PATH)
    tickers = session.query(Ticker).filter_by(active=True).order_by(Ticker.symbol).all()
    session.close()
    if tickers:
        st.metric("Total Active Tickers", len(tickers))
        cols_per_row = 6
        rows = [tickers[i:i+cols_per_row] for i in range(0, len(tickers), cols_per_row)]
        for row in rows:
            cols = st.columns(cols_per_row)
            for j, ticker in enumerate(row):
                with cols[j]:
                    with st.container(border=True):
                        st.markdown(f"**{ticker.symbol}**")
                        st.caption(ticker.sector or "Unknown")
                        if st.button("🗑️", key=f"del_{ticker.symbol}", help=f"Remove {ticker.symbol}"):
                            remove_ticker(ticker.symbol)
                            st.success(f"Removed {ticker.symbol}")
                            st.cache_data.clear()
                            st.rerun()
    else:
        st.info("No active tickers. Add some above.")
except Exception as e:
    st.error(f"Error loading tickers: {e}")

st.divider()

# Bulk add
st.markdown("### 📝 Bulk Add Tickers")
bulk_input = st.text_area("Enter multiple tickers (comma or newline separated)", placeholder="AAPL, MSFT, GOOGL\nNVDA, TSLA")
if st.button("📥 Bulk Add", use_container_width=False):
    symbols = [s.strip().upper() for s in bulk_input.replace("\n", ",").split(",") if s.strip()]
    if symbols:
        progress = st.progress(0)
        results = []
        for i, sym in enumerate(symbols):
            success = add_ticker(sym)
            results.append((sym, success))
            progress.progress((i + 1) / len(symbols))
        st.cache_data.clear()
        ok = [r[0] for r in results if r[1]]
        fail = [r[0] for r in results if not r[1]]
        if ok:
            st.success(f"Added: {', '.join(ok)}")
        if fail:
            st.warning(f"Failed: {', '.join(fail)}")
    else:
        st.warning("No valid tickers found.")
