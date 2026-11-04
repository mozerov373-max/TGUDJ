import os
from datetime import timedelta, timezone

TZ = timezone(timedelta(hours=7))

SCAN_START_H, SCAN_START_M = 13, 0
SCAN_END_H, SCAN_END_M = 17, 30

ASIA_START_H, ASIA_END_H = 4, 11

KILLZONE_START = (14, 30)
KILLZONE_END = (16, 30)
ENFORCE_KILLZONE = True

TWELVEDATA_KEY = "ТВОЙ_КЛЮЧ_TWELVEDATA"  # Вставь сюда ключ с сайта twelvedata.com
INTERVAL = "5min"
HISTORY_BARS = 500
INTERVAL_SEC = 60
FRESH_MIN = 20

BALANCE_DEFAULT = 5000.0
RISK_PCT = 1.0

SWEEP_SL_BUFFER_PIPS = 2
MIN_FVG_PIPS = {
    "EURUSD": 2.0,
    "GBPUSD": 2.0,
}

WIDE_ASIA_PIPS = {
    "EURUSD": 40,
    "GBPUSD": 50,
}
SETUP2_SL_PIPS = 3.5
H1_MIN_FVG_PIPS = 3
H1_MAGNET_PIPS = 5
SKIP_ON_H1_MAGNET = True

SYMBOLS = {
    "EURUSD": dict(td_symbol="EUR/USD", smt_with="DXY", pip=0.0001, usd_lot=True),
    "GBPUSD": dict(td_symbol="GBP/USD", smt_with="DXY", pip=0.0001, usd_lot=True),
}

DXY_SYMBOL = dict(td_symbol="DXY", pip=0.01, usd_lot=False)

# --- TELEGRAM ---
TELEGRAM_TOKEN = "9138322774:AAHzyzJBeDKPWnSwx1INRSp3NK50wPJCbjM"
TELEGRAM_CHAT_ID = "1472962822"

STATE_FILE = "state.json"
