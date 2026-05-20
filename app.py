import streamlit as st
import pandas as pd
from datetime import datetime
from database.models import init_db
from config.settings import APP_NAME, VERSION, DB_PATH

st.set_page_config(
    page_title="Earnings Hunter AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DB
init_db(DB_PATH)

# Inject custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
body, .stApp { font-family: 'Share Tech Mono', monospace !important; background-color: #0D0D0D; }
.main-header { background: linear-gradient(90deg, #0D0D0D 0%, #1A1A1A 100%); border-bottom: 2px solid #00FF41; padding: 1rem; }
.metric-card { background: #1A1A1A; border: 1px solid #00FF41; border-radius: 4px; padding: 1rem; margin: 0.5rem 0; }
.buy-signal { color: #00FF41; font-weight: bold; }
.sell-signal { color: #FF4444; font-weight: bold; }
.watch-signal { color: #FFD700; }
.ticker-badge { background: #0D2B0D; border: 1px solid #00FF41; border-radius: 3px; padding: 2px 8px; color: #00FF41; }
sticker-badge { color: #00FF41; }
[data-testid="stSidebar"] { background: #111111; border-right: 1px solid #1E1E1E; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(f"""
<div class="main-header">
    <h1 style="color:#00FF41; margin:0; font-size:2.2rem;">📈 EARNINGS HUNTER AI</h1>
    <p style="color:#666; margin:0; font-size:0.85rem;">v{VERSION} | Professional Earnings Trading Platform | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Navigation guide
col1, col2, col3 = st.columns(3)
with col1:
    st.info("📊 Use the **sidebar** to navigate between pages")
with col2:
    st.info("🔔 Configure **Telegram alerts** in Alert Center")
with col3:
    st.info("➕ Add tickers in **Ticker Manager**")

st.markdown("---")

# Quick stats
st.subheader("🚀 Quick Navigation")
cols = st.columns(6)
with cols[0]:
    if st.button("📊 Dashboard", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")
with cols[1]:
    if st.button("📅 Calendar", use_container_width=True):
        st.switch_page("pages/2_Earnings_Calendar.py")
with cols[2]:
    if st.button("🎯 Signals", use_container_width=True):
        st.switch_page("pages/3_Signals_Center.py")
with cols[3]:
    if st.button("➕ Tickers", use_container_width=True):
        st.switch_page("pages/4_Ticker_Manager.py")
with cols[4]:
    if st.button("🔔 Alerts", use_container_width=True):
        st.switch_page("pages/5_Alert_Center.py")
with cols[5]:
    if st.button("📈 Analytics", use_container_width=True):
        st.switch_page("pages/6_Analytics.py")

st.markdown("---")
st.markdown('''
<div style="text-align:center; color:#333; font-size:0.8rem;">
Earnings Hunter AI | Built with Streamlit | Bloomberg-Style Terminal
</div>
''', unsafe_allow_html=True)
