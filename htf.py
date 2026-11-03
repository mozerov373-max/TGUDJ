"""D1/H4 контекст: State A (тренд) / B (диапазон) / C (разворот на границе)."""
import pandas as pd
from .data import to_d1
def d1_state(closed: pd.DataFrame, now) -> dict:
    d1 = to_d1(closed, now)
    if len(d1) < 10:
        return {"state": "?", "bias": None, "range": None}
    recent = d1.tail(15)
    last10 = recent.tail(10)
    h_range = last10.h.max() - last10.h.min()
    l_range = last10.l.max() - last10.l.min()
    avg_range = (last10.h.max() - last10.l.min())
    if avg_range > 0 and (h_range / avg_range < 0.35) and (l_range / avg_range < 0.35):
        return {
            "state": "B",
            "bias": None,
            "range": (float(last10.h.max()), float(last10.l.min())),
        }
    sw = _swings(recent, left=1, right=1)
    if len(sw["highs"]) >= 2 and len(sw["lows"]) >= 2:
        hh = all(sw["highs"][i] < sw["highs"][i + 1] for i in range(len(sw["highs"]) - 1))
        hl = all(sw["lows"][i] < sw["lows"][i + 1] for i in range(len(sw["lows"]) - 1))
        ll = all(sw["highs"][i] > sw["highs"][i + 1] for i in range(len(sw["highs"]) - 1))
        lh = all(sw["lows"][i] > sw["lows"][i + 1] for i in range(len(sw["lows"]) - 1))
        if hh and hl:
            return {"state": "A", "bias": "long", "range": None}
        if ll and lh:
            return {"state": "A", "bias": "short", "range": None}
    last20 = recent.tail(20)
    d1_hi = float(last20.h.max())
    d1_lo = float(last20.l.min())
    last_close = float(d1.c.iloc[-1])
    near_hi = (d1_hi - last_close) / d1_hi < 0.003
    near_lo = (last_close - d1_lo) / d1_lo < 0.003
    h4 = _to_h4(closed, now)
    if near_hi and _mss_down(h4):
        return {"state": "C", "bias": "short", "range": (d1_hi, d1_lo)}
    if near_lo and _mss_up(h4):
        return {"state": "C", "bias": "long", "range": (d1_hi, d1_lo)}
    return {"state": "?", "bias": None, "range": None}
def _to_h4(closed, now):
    h4 = closed.resample("4h").agg({"o": "first", "h": "max", "l": "min", "c": "last"}).dropna()
    return h4[h4.index + pd.Timedelta(hours=4) <= now]
def _mss_down(h4):
    if len(h4) < 5:
        return False
    c = h4.c.values
    lows = h4.l.values
    for i in range(len(h4) - 1, 2, -1):
        sw = lows[i - 2]
        if c[i] < sw and c[i - 1] > sw - 0.0001:
            return True
    return False
def _mss_up(h4):
    if len(h4) < 5:
        return False
    c = h4.c.values
    highs = h4.h.values
    for i in range(len(h4) - 1, 2, -1):
        sw = highs[i - 2]
        if c[i] > sw and c[i - 1] < sw + 0.0001:
            return True
    return False
def _swings(df, left=1, right=1):
    h = df.h.values
    l = df.l.values
    highs, lows = [], []
    for i in range(left, len(df) - right):
        if all(h[i] > h[i - k] for k in range(1, left + 1)) and            all(h[i] > h[i + k] for k in range(1, right + 1)):
            highs.append(float(h[i]))
        if all(l[i] < l[i - k] for k in range(1, left + 1)) and            all(l[i] < l[i + k] for k in range(1, right + 1)):
            lows.append(float(l[i]))
    return {"highs": highs, "lows": lows}
def htf_allows(direction: str, d1_info: dict) -> bool:
    state = d1_info["state"]
    bias = d1_info["bias"]
    if state == "A":
        return bias == direction
    if state == "B":
        return True
    if state == "C":
        return bias == direction
    return False
