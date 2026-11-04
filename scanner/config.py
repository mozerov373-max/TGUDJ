"""Все настройки AES scanner в одном месте."""
import os
from datetime import timedelta, timezone

# ---------- Таймзона ----------
TZ = timezone(timedelta(hours=7))  # Барнаул, UTC+7

# ---------- Окно сканирования (Барнаул) ----------
SCAN_START_H, SCAN_START_M = 13, 0
SCAN_END_H, SCAN_END_M = 17, 30

# ---------- Азиатский бокс ----------
ASIA_START_H, ASIA_END_H = 4, 11

# ---------- Kill Zone (по ТЗ) ----------
KILLZONE_START = (14, 30)
KILLZONE_END = (16, 30)
ENFORCE_KILLZONE = True

# ---------- Данные ----------
TWELVEDATA_KEY = os.getenv("TWELVEDATA_KEY", "").strip()
INTERVAL = "5min"
HISTORY_BARS = 500
INTERVAL_SEC = 60
FRESH_MIN = 20

# ---------- Риск (динамический) ----------
_bal_env = os.getenv("BALANCE", "5000").strip()
BALANCE_DEFAULT = float(_bal_env) if _bal_env else 5000.0
RISK_PCT = 1.0

# ---------- Сетап №1 ----------
SWEEP_SL_BUFFER_PIPS = 2
MIN_FVG_PIPS = {
    "EURUSD": 2.0,
    "GBPUSD": 2.0,
}

# ---------- Сетап №2 ----------
WIDE_ASIA_PIPS = {
    "EURUSD": 40,
    "GBPUSD": 50,
}
SETUP2_SL_PIPS = 3.5
H1_MIN_FVG_PIPS = 3
H1_MAGNET_PIPS = 5
SKIP_ON_H1_MAGNET = True

# ---------- Инструменты ----------
SYMBOLS = {
    "EURUSD": dict(
        td_symbol="EUR/USD",
        smt_with="DXY",
        pip=0.0001,
        usd_lot=True,
    ),
    "GBPUSD": dict(
        td_symbol="GBP/USD",
        smt_with="DXY",
        pip=0.0001,
        usd_lot=True,
    ),
}

DXY_SYMBOL = dict(
    td_symbol="DXY",
    pip=0.01,
    usd_lot=False,
)

# ---------- Telegram (с очисткой от пробелов) ----------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# ---------- State ----------
STATE_FILE = os.getenv("STATE_FILE", "state.json")