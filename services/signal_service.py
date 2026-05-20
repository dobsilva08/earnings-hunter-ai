import pandas as pd
from datetime import datetime
from database.models import init_db, get_session, Signal, EarningsDate
from utils.dates import trading_days_until_earnings
from utils.logger import logger
from config.settings import BUY_SIGNAL_DAYS, SELL_SIGNAL_DAYS, DB_PATH
import yfinance as yf


def get_current_price(symbol: str) -> float:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            return round(float(hist["Close"].iloc[-1]), 2)
    except Exception:
        pass
    return 0.0


def evaluate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Add signal status to earnings DataFrame."""
    if df.empty:
        return df
    df = df.copy()
    df["trading_days"] = df["earnings_date"].apply(trading_days_until_earnings)
    
    def get_signal(days):
        if days < 0:
            return "PASSED"
        elif days <= SELL_SIGNAL_DAYS:
            return "SELL"
        elif days <= BUY_SIGNAL_DAYS:
            return "BUY"
        else:
            return "WATCH"
    
    df["signal"] = df["trading_days"].apply(get_signal)
    return df


def save_signals_to_db(df: pd.DataFrame):
    """Save active signals to DB."""
    if df.empty:
        return
    init_db(DB_PATH)
    session = get_session(DB_PATH)
    try:
        active_signals = df[df["signal"].isin(["BUY", "SELL"])]
        for _, row in active_signals.iterrows():
            existing = session.query(Signal).filter_by(
                symbol=row["symbol"],
                signal_type=row["signal"],
                earnings_date=row["earnings_date"]
            ).first()
            if not existing:
                price = get_current_price(row["symbol"])
                signal = Signal(
                    symbol=row["symbol"],
                    signal_type=row["signal"],
                    signal_date=datetime.utcnow(),
                    earnings_date=row["earnings_date"],
                    days_to_earnings=row["trading_days"],
                    price_at_signal=price,
                    active=True,
                    sent_telegram=False
                )
                session.add(signal)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving signals: {e}")
    finally:
        session.close()


def get_active_signals(signal_type: str = None) -> pd.DataFrame:
    """Get active signals from DB."""
    try:
        session = get_session(DB_PATH)
        query = session.query(Signal).filter_by(active=True)
        if signal_type:
            query = query.filter_by(signal_type=signal_type)
        signals = query.order_by(Signal.signal_date.desc()).all()
        session.close()
        if not signals:
            return pd.DataFrame()
        data = [{
            "id": s.id,
            "symbol": s.symbol,
            "signal_type": s.signal_type,
            "signal_date": s.signal_date,
            "earnings_date": s.earnings_date,
            "days_to_earnings": s.days_to_earnings,
            "price_at_signal": s.price_at_signal,
            "sent_telegram": s.sent_telegram
        } for s in signals]
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error loading signals: {e}")
        return pd.DataFrame()


def get_signal_color(signal: str) -> str:
    colors = {"BUY": "#00FF41", "SELL": "#FF4444", "WATCH": "#FFD700", "PASSED": "#666666"}
    return colors.get(signal, "#FFFFFF")
