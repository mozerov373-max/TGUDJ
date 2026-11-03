"""Фильтры: H1 FVG-магнит, Kill Zone, лоты, форматирование."""
from datetime import datetime
from .config import (
    KILLZONE_START, KILLZONE_END, ENFORCE_KILLZONE,
    H1_MAGNET_PIPS, RISK_PCT,
)
def in_killzone(now: datetime) -> bool:
    m = now.hour * 60 + now.minute
    a = KILLZONE_START[0] * 60 + KILLZONE_START[1]
    b = KILLZONE_END[0] * 60 + KILLZONE_END[1]
    return a <= m <= b
def killzone_ok(now: datetime) -> bool:
    return (not ENFORCE_KILLZONE) or in_killzone(now)
def h1_fvgs(h1) -> list[dict]:
    res = []
    h, l = h1.h.values, h1.l.values
    for i in range(2, len(h1)):
        if h[i - 2] < l[i]:
            res.append(dict(dir="up", bot=float(h[i - 2]), top=float(l[i]),
                            mid_t=h1.index[i - 1],
                            end_t=h1.index[i]))
        elif l[i - 2] > h[i]:
            res.append(dict(dir="down", bot=float(h[i]), top=float(l[i - 2]),
                            mid_t=h1.index[i - 1],
                            end_t=h1.index[i]))
    return res
def opposing_h1_magnet(full, direction, entry, tp, pip):
    h1 = full.resample("1h").agg({"o": "first", "h": "max", "l": "min", "c": "last"}).dropna()
    fvgs = h1_fvgs(h1)
    for g in fvgs:
        if (g["top"] - g["bot"]) / pip <= H1_MAGNET_PIPS:
            continue
        after = full[full.index >= g["end_t"]]
        if direction == "short" and g["dir"] == "up" and tp < g["top"] < entry:
            if after.empty or after.l.min() > g["bot"]:
                return g
        if direction == "long" and g["dir"] == "down" and entry < g["bot"] < tp:
            if after.empty or after.h.max() < g["top"]:
                return g
    return None
def lot_text(cfg, balance, risk_pips):
    if not cfg["usd_lot"] or risk_pips <= 0:
        return ""
    lots = balance * RISK_PCT / 100 / (risk_pips * 10)
    return f"\nРиск {RISK_PCT:.0f}% = ${balance*RISK_PCT/100:.0f} → ~{lots:.2f} лота"
def fmt(p, pip):
    return f"{p:.5f}" if pip < 0.001 else f"{p:.2f}"
