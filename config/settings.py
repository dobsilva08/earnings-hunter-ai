import os
from dotenv import load_dotenv

load_dotenv()

# App
APP_NAME = os.getenv("APP_NAME", "Earnings Hunter AI")
VERSION = "1.0.0"

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Trading rules
BUY_SIGNAL_DAYS = 10   # E-10
SELL_SIGNAL_DAYS = 2   # E-2

# Scheduler
UPDATE_HOUR = int(os.getenv("UPDATE_HOUR", 6))
UPDATE_MINUTE = int(os.getenv("UPDATE_MINUTE", 0))
INTRADAY_INTERVAL_MINUTES = 60

# Database
DB_PATH = "database/earnings_hunter.db"

# Default tickers
DEFAULT_TICKERS = [
    # Tech Giants
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "AMD", "NFLX", "CRM",
    "ORCL", "INTC", "QCOM", "AVGO", "MU",
    # Finance
    "JPM", "GS", "MS", "BAC", "V",
    # User Added
    "SHOP", "PLTR", "QBTS", "CVNA", "TWLO",
    "LRCX", "QUBT", "MRNA", "SEDG", "CIFR",
    "AMPX", "GENI", "BORR", "DLO", "IOT",
    "TROX", "NBR", "PGEN", "UUUU", "RMTI",
    "OPEN", "RZLV", "GRPO", "SLNH", "LEU",
    "SES", "SMTC", "USAR", "FATN", "CSCO",
    "APM", "FLNC", "ASTS", "ABCD",
]

# API settings
RATE_LIMIT_DELAY = 0.5
MAX_RETRIES = 3
RETRY_BACKOFF = 2
