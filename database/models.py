from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Ticker(Base):
    __tablename__ = "tickers"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False)
    name = Column(String(100))
    sector = Column(String(50))
    active = Column(Boolean, default=True)
    added_at = Column(DateTime, default=datetime.utcnow)

class EarningsDate(Base):
    __tablename__ = "earnings_dates"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    earnings_date = Column(DateTime, nullable=False)
    timing = Column(String(10))  # AMC or BMO
    source = Column(String(50))
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    signal_type = Column(String(10), nullable=False)  # BUY or SELL
    signal_date = Column(DateTime, nullable=False)
    earnings_date = Column(DateTime, nullable=False)
    days_to_earnings = Column(Integer)
    price_at_signal = Column(Float)
    active = Column(Boolean, default=True)
    sent_telegram = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AlertLog(Base):
    __tablename__ = "alert_logs"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10))
    alert_type = Column(String(50))
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    date = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

def get_engine(db_path="database/earnings_hunter.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False)

def init_db(db_path="database/earnings_hunter.db"):
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine

def get_session(db_path="database/earnings_hunter.db"):
    engine = get_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()
