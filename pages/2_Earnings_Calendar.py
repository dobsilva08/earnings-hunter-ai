import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from services.earnings_service import get_all_earnings, load_tickers_from_db, seed_default_tickers
from services.signal_service import evaluate_signals
from database.models import init_db
from config.settings import DB_PATH

st.set_page_config(page_title="Earnings Calendar", page_icon="📅", layout="wide")
st.title("📅 Earnings Calendar")

init_db(DB_PATH)
seed_default_tickers()

@st.cache_data(ttl=3600, show_spinner="Loading calendar...")
def load_calendar():
    tickers = load_tickers_from_db()
    df = get_all_earnings(tickers)
    if not df.empty:
        df = evaluate_signals(df)
    return df

df = load_calendar()

if df.empty:
    st.warning("No earnings data available. Go to Dashboard and click Fetch Earnings Now.")
    st.stop()

df["earnings_date"] = pd.to_datetime(df["earnings_date"])

# Filters
col1, col2 = st.columns(2)
with col1:
    days_ahead = st.slider("Show next N days", 7, 90, 30)
with col2:
    sectors = ["All"] + sorted(df["sector"].dropna().unique().tolist()) if "sector" in df.columns else ["All"]
    selected_sector = st.selectbox("Filter by Sector", sectors)

cutoff = pd.Timestamp.now() + timedelta(days=days_ahead)
filtered = df[df["earnings_date"] <= cutoff].copy()
if selected_sector != "All" and "sector" in filtered.columns:
    filtered = filtered[filtered["sector"] == selected_sector]

# Calendar view by week
st.markdown("### 📆 Weekly View")
weeks = pd.date_range(start=pd.Timestamp.now().date(), periods=6, freq="W-MON")
for i, week_start in enumerate(weeks):
    week_end = week_start + timedelta(days=4)
    week_df = filtered[(filtered["earnings_date"] >= week_start) & (filtered["earnings_date"] <= week_end)]
    if week_df.empty:
        continue
    with st.expander(f"Week of {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')} ({len(week_df)} earnings)", expanded=(i == 0)):
        days = pd.date_range(start=week_start, end=week_end, freq="D")
        day_cols = st.columns(5)
        for j, day in enumerate(days):
            day_data = week_df[week_df["earnings_date"].dt.date == day.date()]
            with day_cols[j]:
                st.markdown(f"**{day.strftime('%a %m/%d')}**")
                if day_data.empty:
                    st.caption("—")
                else:
                    for _, row in day_data.iterrows():
                        sig = row.get("signal", "WATCH")
                        color = "#00FF41" if sig == "BUY" else "#FF4444" if sig == "SELL" else "#FFD700"
                        timing = row.get("timing", "AMC")
                        st.markdown(f'<span style="color:{color}; font-weight:bold;">{row["symbol"]}</span> <small style="color:#666;">({timing})</small>', unsafe_allow_html=True)

st.divider()

# Full table view
st.markdown("### 📋 Full Earnings List")
cols_show = [c for c in ["symbol", "name", "earnings_date", "trading_days", "signal", "timing", "sector"] if c in filtered.columns]
if not filtered.empty:
    display = filtered[cols_show].copy()
    if "earnings_date" in display.columns:
        display["earnings_date"] = display["earnings_date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display.sort_values("earnings_date") if "earnings_date" in display.columns else display,
                 use_container_width=True, height=400)
