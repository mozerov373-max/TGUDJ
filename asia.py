"""Азиатский бокс."""
from datetime import datetime
import pandas as pd
from .config import ASIA_START_H, ASIA_END_H, TZ
def asia_box(closed: pd.DataFrame, now: datetime):
    day = now.date()
    start = datetime(day.year, day.month, day.day, ASIA_START_H, tzinfo=TZ)
    end = datetime(day.year, day.month, day.day, ASIA_END_H, tzinfo=TZ)
    box = closed[(closed.index >= start) & (closed.index < end)]
    if len(box) < 40:
        return None
    return {
        "high": float(box.h.max()),
        "low": float(box.l.min()),
        "mid": float((box.h.max() + box.l.min()) / 2),
        "start": start,
        "end": end,
        "bars": box,
    }
