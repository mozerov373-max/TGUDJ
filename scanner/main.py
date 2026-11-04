"""//Оркестратор AES scanner — DXY только при кандидате//"""
import argparse
import sys
import time
import traceback
from datetime import datetime, timedelta
from .config import (
    TZ, SCAN_START_H, SCAN_START_M, SCAN_END_H, SCAN_END_M,
    INTERVAL_SEC, SYMBOLS, DXY_SYMBOL,
)
from .data import fetch_5m, closed_only
from .asia import asia_box
from .htf import d1_state
from .filters import in_killzone
from .setups import (
    find_setup1_candidate, finalize_setup1,
    find_setup2_candidate, finalize_setup2,
)
from .state import load, save
from .telegram import telegram
from .log import log
def _scan_now(now, state):
    sent_keys = set(state["sent_keys"])
    candidates = []
    errors = 0
    for name, cfg in SYMBOLS.items():
        try:
            full = fetch_5m(cfg["td_symbol"])
            closed = closed_only(full, now)
            asia = asia_box(closed, now)
            if asia is None:
                log(f"{name}: мало данных по Азии")
                continue
            d1_info = d1_state(closed, now)
            c1 = find_setup1_candidate(name, cfg, closed, full, asia, now,
                                       d1_info, state["balance"], sent_keys)
            if c1:
                candidates.append(("S1", c1))
            c2 = find_setup2_candidate(name, cfg, closed, full, asia, now,
                                       d1_info, state["balance"], sent_keys)
            if c2:
                candidates.append(("S2", c2))
        except Exception:
            errors += 1
            log(f"{name} ошибка:", traceback.format_exc().splitlines()[-1])
    if candidates:
        dxy_closed = None
        try:
            dxy_full = fetch_5m(DXY_SYMBOL["td_symbol"])
            dxy_closed = closed_only(dxy_full, now)
        except Exception as e:
            log("DXY ошибка:", e)
            errors += 1
        for tag, c in candidates:
            try:
                if tag == "S1":
                    finalize_setup1(c, dxy_closed, sent_keys)
                else:
                    finalize_setup2(c, dxy_closed, sent_keys)
            except Exception:
                errors += 1
                log(f"finalize {tag} ошибка:",
                    traceback.format_exc().splitlines()[-1])
    else:
        log("кандидатов нет — DXY не грузим")
    state["sent_keys"] = list(sent_keys)
    return errors
def _check_cushion(now, state):
    if not state["cushion_watch"]:
        return
    still = []
    for w in state["cushion_watch"]:
        try:
            full = fetch_5m(w["symbol"])
            closed = closed_only(full, now)
            last = float(closed.c.iloc[-1])
            mid = w["mid"]
            if (w["direction"] == "short" and last > mid) or                (w["direction"] == "long" and last < mid):
                telegram(
                    f"⚠️ <b>Cushion SL активирован</b> — {w['symbol']}\n"
                    f"{w['direction'].upper()} вход {w['entry']:.5f}\n"
                    f"Midpoint Азии: {mid:.5f} пробит против сделки\n"
                    f"<b>Сожми SL до −5 п. от входа</b>"
                )
                log("cushion отправлен", w["symbol"])
                continue
            still.append(w)
        except Exception as e:
            log("cushion error:", e)
            still.append(w)
    state["cushion_watch"] = still
def run_once(state):
    now = datetime.now(TZ)
    if not in_killzone(now):
        return 0
    return _scan_now(now, state)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--balance", type=float, default=None)
    args = ap.parse_args()
    if args.test:
        ok = telegram("✅ AES scanner: тест связи прошёл.")
        sys.exit(0 if ok else 1)
    state = load()
    if args.balance is not None:
        state["balance"] = args.balance
        save(state)
        telegram(f"💰 Баланс обновлён: ${args.balance:.2f}")
        return
    if args.once:
        run_once(state)
        save(state)
        return
    t0 = datetime.now(TZ)
    day = t0.date()
    w_start = datetime(day.year, day.month, day.day,
                       SCAN_START_H, SCAN_START_M, tzinfo=TZ)
    w_end = datetime(day.year, day.month, day.day,
                     SCAN_END_H, SCAN_END_M, tzinfo=TZ)
    deadline = min(w_end, t0 + timedelta(hours=5, minutes=30))
    if t0.weekday() >= 5 or t0 >= w_end:
        log("вне окна, выход")
        return
    if t0 < w_start:
        wait = (w_start - t0).total_seconds()
        log(f"жду {wait:.0f} сек до {w_start:%H:%M}")
        time.sleep(max(0, wait))
    telegram(
        f"🟢 AES сканер запущен {datetime.now(TZ):%H:%M} Барнаул\n"
        f"EURUSD / GBPUSD, окно до {deadline:%H:%M}, Kill Zone 14:30–16:30\n"
        f"Баланс: ${state['balance']:.2f}\n"
        f"<i>DXY грузится только при кандидате (экономия лимита)</i>"
    )
    fails = 0
    while datetime.now(TZ) < deadline:
        started = time.time()
        errs = _scan_now(datetime.now(TZ), state)
        fails = fails + 1 if errs >= len(SYMBOLS) else 0
        if fails == 10:
            telegram("⚠️ 10 минут подряд нет данных (TwelveData?).")
        _check_cushion(datetime.now(TZ), state)
        save(state)
        time.sleep(max(1, INTERVAL_SEC - (time.time() - started)))
    save(state)
    telegram(f"🔴 AES сканер завершил работу {datetime.now(TZ):%H:%M}.")
if __name__ == "__main__":
    main()
