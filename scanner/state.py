"""Persist состояния между запусками."""
import json
import os
from .config import STATE_FILE, BALANCE_DEFAULT
from .log import log
def load() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("balance", BALANCE_DEFAULT)
            data.setdefault("sent_keys", [])
            data.setdefault("cushion_watch", [])
            return data
        except Exception as e:
            log("state load error:", e)
    return {
        "balance": BALANCE_DEFAULT,
        "sent_keys": [],
        "cushion_watch": [],
    }
def save(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log("state save error:", e)
