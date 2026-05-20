import requests
from database.models import init_db, get_session, AlertLog
from utils.logger import logger
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DB_PATH
from datetime import datetime


def send_telegram_message(message: str, token: str = None, chat_id: str = None) -> bool:
    """Send a message via Telegram Bot API."""
    token = token or TELEGRAM_BOT_TOKEN
    chat_id = chat_id or TELEGRAM_CHAT_ID
    if not token or not chat_id:
        logger.warning("Telegram not configured.")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            _log_alert("TELEGRAM", message, True)
            return True
        _log_alert("TELEGRAM", message, False)
        return False
    except Exception as e:
        _log_alert("TELEGRAM", str(e), False)
        return False


def send_signal_alert(symbol, signal_type, earnings_date, days, price, token=None, chat_id=None):
    emoji = "BUY SIGNAL" if signal_type == "BUY" else "SELL SIGNAL"
    msg = f"EARNINGS HUNTER AI\n{emoji}\nTicker: {symbol}\nEarnings: {str(earnings_date)[:10]}\nE-{days}\nPrice: ${price:.2f}"
    return send_telegram_message(msg, token, chat_id)


def _log_alert(alert_type, message, success):
    try:
        init_db(DB_PATH)
        session = get_session(DB_PATH)
        log = AlertLog(alert_type=alert_type, message=message[:500], success=success)
        session.add(log)
        session.commit()
        session.close()
    except Exception:
        pass


def get_alert_logs(limit=100):
    try:
        session = get_session(DB_PATH)
        logs = session.query(AlertLog).order_by(AlertLog.sent_at.desc()).limit(limit).all()
        session.close()
        return [{"type": l.alert_type, "message": l.message[:100], "sent_at": l.sent_at, "success": l.success} for l in logs]
    except Exception:
        return []
