import streamlit as st
import pandas as pd
from services.telegram_service import send_telegram_message, get_alert_logs
from database.models import init_db
from config.settings import DB_PATH, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

st.set_page_config(page_title="Alert Center", page_icon="🔔", layout="wide")
st.title("🔔 Alert Center")

init_db(DB_PATH)

tab1, tab2 = st.tabs(["⚙️ Telegram Config", "📜 Alert Logs"])

with tab1:
    st.markdown("### Telegram Bot Configuration")
    st.info("To use Telegram alerts: 1) Create a bot with @BotFather 2) Get your Chat ID 3) Configure below")
    
    col1, col2 = st.columns(2)
    with col1:
        bot_token = st.text_input("Telegram Bot Token", value=TELEGRAM_BOT_TOKEN or "", type="password",
                                   placeholder="123456789:ABCDef...")
    with col2:
        chat_id = st.text_input("Chat ID / Channel ID", value=TELEGRAM_CHAT_ID or "",
                                 placeholder="-1001234567890")
    
    st.markdown("---")
    st.markdown("### Test Connection")
    test_msg = st.text_input("Test message", value="Hello from Earnings Hunter AI! 📈")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧪 Send Test Message", type="primary", use_container_width=True):
            if bot_token and chat_id:
                with st.spinner("Sending..."):
                    result = send_telegram_message(test_msg, token=bot_token, chat_id=chat_id)
                if result:
                    st.success("✅ Test message sent successfully!")
                else:
                    st.error("❌ Failed to send. Check your token and chat ID.")
            else:
                st.warning("Please enter Bot Token and Chat ID first.")
    with col2:
        if st.button("💾 Save Config to .env", use_container_width=True):
            try:
                with open(".env", "w") as f:
                    f.write(f"TELEGRAM_BOT_TOKEN={bot_token}\n")
                    f.write(f"TELEGRAM_CHAT_ID={chat_id}\n")
                st.success("Config saved to .env — restart app to apply")
            except Exception as e:
                st.error(f"Error saving: {e}")
    
    st.markdown("---")
    st.markdown("### 📖 How to get your Chat ID")
    st.markdown("""
    1. Start a conversation with your bot
    2. Send any message to it
    3. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
    4. Find the `chat.id` in the response
    
    **For channels**: Add bot as admin, then use the channel username or negative ID
    """)

with tab2:
    st.markdown("### 📜 Alert History")
    logs = get_alert_logs(limit=100)
    if not logs:
        st.info("No alerts sent yet.")
    else:
        df = pd.DataFrame(logs)
        if "sent_at" in df.columns:
            df["sent_at"] = pd.to_datetime(df["sent_at"]).dt.strftime("%Y-%m-%d %H:%M")
        def color_success(val):
            return "color: #00FF41" if val else "color: #FF4444"
        st.dataframe(
            df.style.applymap(color_success, subset=["success"] if "success" in df.columns else []),
            use_container_width=True,
            height=500
        )
