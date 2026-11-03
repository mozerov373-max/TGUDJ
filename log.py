"""Простое логирование с временем Барнаула."""
from datetime import datetime
from .config import TZ
def log(*args):
    print(datetime.now(TZ).strftime("%H:%M:%S"), *args, flush=True)
