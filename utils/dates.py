from datetime import datetime, timedelta
import pytz
import pandas as pd
import yfinance as yf

def get_trading_days_between(start_date, end_date):
    """Return number of trading days between two dates."""
    try:
        dates = pd.bdate_range(start=start_date, end=end_date)
        return len(dates)
    except Exception:
        delta = (end_date - start_date).days
        return max(0, int(delta * 5 / 7))

def get_date_n_trading_days_before(target_date, n_days):
    """Get date that is n trading days before target_date."""
    try:
        current = target_date
        count = 0
        while count < n_days:
            current -= timedelta(days=1)
            if current.weekday() < 5:  # Mon-Fri
                count += 1
        return current
    except Exception:
        return target_date - timedelta(days=int(n_days * 7 / 5))

def days_until_earnings(earnings_date):
    """Return calendar days until earnings."""
    now = datetime.now()
    if isinstance(earnings_date, str):
        earnings_date = pd.to_datetime(earnings_date)
    if hasattr(earnings_date, 'tzinfo') and earnings_date.tzinfo:
        earnings_date = earnings_date.replace(tzinfo=None)
    return (earnings_date - now).days

def trading_days_until_earnings(earnings_date):
    """Return trading days until earnings."""
    now = datetime.now().date()
    if isinstance(earnings_date, str):
        earnings_date = pd.to_datetime(earnings_date).date()
    elif hasattr(earnings_date, 'date'):
        earnings_date = earnings_date.date()
    return get_trading_days_between(now, earnings_date)

def format_date(dt):
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        dt = pd.to_datetime(dt)
    return dt.strftime("%Y-%m-%d")

def is_market_open():
    """Check if US market is currently open."""
    et = pytz.timezone('America/New_York')
    now_et = datetime.now(et)
    if now_et.weekday() >= 5:
        return False
    market_open = now_et.replace(hour=9, minute=30, second=0)
    market_close = now_et.replace(hour=16, minute=0, second=0)
    return market_open <= now_et <= market_close
