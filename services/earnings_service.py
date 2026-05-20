import yfinance as yf
import pandas as pd
import time
import streamlit as st
from datetime import datetime, timedelta
from database.models import init_db, get_session, EarningsDate, Ticker
from utils.logger import logger
from config.settings import DEFAULT_TICKERS, RATE_LIMIT_DELAY, MAX_RETRIES, RETRY_BACKOFF, DB_PATH


def get_earnings_date(symbol: str, retries=MAX_RETRIES) -> dict:
    """Fetch next earnings date for a symbol using yfinance."""
    for attempt in range(retries):
        try:
            ticker = yf.Ticker(symbol)
            cal = ticker.calendar
            info = ticker.info
            earnings_date = None
            timing = "AMC"
            if cal is not None and not (isinstance(cal, pd.DataFrame) and cal.empty):
                if isinstance(cal, pd.DataFrame):
                    if "Earnings Date" in cal.index:
                        val = cal.loc["Earnings Date"]
                        if hasattr(val, '__iter__'):
                            earnings_date = pd.to_datetime(val.iloc[0]) if len(val) > 0 else None
                        else:
                            earnings_date = pd.to_datetime(val)
                elif isinstance(cal, dict):
                    if "Earnings Date" in cal:
                        dates = cal["Earnings Date"]
                        if isinstance(dates, list) and len(dates) > 0:
                            earnings_date = pd.to_datetime(dates[0])
            if earnings_date is None:
                q = ticker.quarterly_earnings
                if q is not None and not q.empty:
                    future = q[q.index > pd.Timestamp.now()]
                    if not future.empty:
                        earnings_date = future.index[0]
            name = info.get("longName", info.get("shortName", symbol))
            sector = info.get("sector", "Unknown")
            return {
                "symbol": symbol,
                "earnings_date": earnings_date,
                "timing": timing,
                "name": name,
                "sector": sector,
                "success": True
            }
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/{retries} failed for {symbol}: {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_BACKOFF ** attempt)
    return {"symbol": symbol, "earnings_date": None, "success": False}


def get_all_earnings(symbols: list = None) -> pd.DataFrame:
    """Fetch earnings dates for all symbols and return as DataFrame."""
    if symbols is None:
        session = get_session(DB_PATH)
        tickers = session.query(Ticker).filter_by(active=True).all()
        symbols = [t.symbol for t in tickers]
        session.close()
        if not symbols:
            symbols = DEFAULT_TICKERS
    results = []
    for symbol in symbols:
        data = get_earnings_date(symbol)
        results.append(data)
        time.sleep(RATE_LIMIT_DELAY)
    df = pd.DataFrame(results)
    if df.empty:
        return df
    df = df[df["earnings_date"].notna()]
    df["earnings_date"] = pd.to_datetime(df["earnings_date"])
    df = df[df["earnings_date"] >= pd.Timestamp.now() - timedelta(days=1)]
    df = df.sort_values("earnings_date").reset_index(drop=True)
    return df


def save_earnings_to_db(df: pd.DataFrame):
    """Save earnings dates to SQLite database."""
    if df.empty:
        return
    session = get_session(DB_PATH)
    try:
        for _, row in df.iterrows():
            existing = session.query(EarningsDate).filter_by(
                symbol=row["symbol"],
                earnings_date=row["earnings_date"]
            ).first()
            if existing:
                existing.updated_at = datetime.utcnow()
            else:
                record = EarningsDate(
                    symbol=row["symbol"],
                    earnings_date=row["earnings_date"],
                    timing=row.get("timing", "AMC"),
                    source="yfinance",
                    confirmed=False
                )
                session.add(record)
        session.commit()
        logger.info(f"Saved {len(df)} earnings dates to DB")
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving earnings: {e}")
    finally:
        session.close()


def load_tickers_from_db() -> list:
    """Load active tickers from DB."""
    try:
        init_db(DB_PATH)
        session = get_session(DB_PATH)
        tickers = session.query(Ticker).filter_by(active=True).all()
        result = [t.symbol for t in tickers]
        session.close()
        if not result:
            seed_default_tickers()
            return DEFAULT_TICKERS
        return result
    except Exception as e:
        logger.error(f"Error loading tickers: {e}")
        return DEFAULT_TICKERS


def seed_default_tickers():
    """Seed the DB with default tickers if empty."""
    try:
        init_db(DB_PATH)
        session = get_session(DB_PATH)
        for symbol in DEFAULT_TICKERS:
            if not session.query(Ticker).filter_by(symbol=symbol).first():
                session.add(Ticker(symbol=symbol))
        session.commit()
        session.close()
    except Exception as e:
        logger.error(f"Error seeding tickers: {e}")


def add_ticker(symbol: str) -> bool:
    try:
        init_db(DB_PATH)
        session = get_session(DB_PATH)
        symbol = symbol.upper().strip()
        existing = session.query(Ticker).filter_by(symbol=symbol).first()
        if existing:
            existing.active = True
            session.commit()
        else:
            info = yf.Ticker(symbol).info
            name = info.get("longName", info.get("shortName", symbol))
            sector = info.get("sector", "Unknown")
            session.add(Ticker(symbol=symbol, name=name, sector=sector))
            session.commit()
        session.close()
        return True
    except Exception as e:
        logger.error(f"Error adding ticker {symbol}: {e}")
        return False


def remove_ticker(symbol: str) -> bool:
    try:
        session = get_session(DB_PATH)
        ticker = session.query(Ticker).filter_by(symbol=symbol).first()
        if ticker:
            ticker.active = False
            session.commit()
        session.close()
        return True
    except Exception as e:
        logger.error(f"Error removing ticker {symbol}: {e}")
        return False
