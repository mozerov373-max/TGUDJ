"""Сетапы №1 и №2. DXY грузится только при наличии геометрического кандидата."""
from datetime import timedelta
from .config import (
    MIN_FVG_PIPS, SWEEP_SL_BUFFER_PIPS, SETUP2_SL_PIPS,
    H1_MIN_FVG_PIPS, WIDE_ASIA_PIPS, FRESH_MIN,
    SKIP_ON_H1_MAGNET,
)
from .data import mirror, to_h1
from .filters import (
    h1_fvgs, opposing_h1_magnet, lot_text, fmt, killzone_ok,
)
from .smt import smt_confirms
from .htf import htf_allows
from .telegram import telegram
from .log import log


def _swing_lows(L, left=2, right=2):
    out = []
    for i in range(left, len(L) - right):
        if all(L[i] < L[i - k] for k in range(1, left + 1)) and \
           all(L[i] < L[i + k] for k in range(1, right + 1)):
            out.append(i)
    return out


def _detect_short_reversal(df, asia_end, AH, AL, pip, min_fvg):
    H, L, C = df.h.values, df.l.values, df.c.values
    n = len(df)
    pos = [i for i, t in enumerate(df.index) if t >= asia_end]
    if not pos:
        return None
    start = pos[0]
    s = next((i for i in range(start, n) if H[i] > AH), None)
    if s is None:
        return None
    piv = _swing_lows(L)
    ext = s
    mss = ref = None
    for j in range(s, n):
        if H[j] > H[ext]:
            ext = j
        if j == ext:
            continue
        cands = [p for p in piv if p + 2 <= ext and p >= ext - 48]
        if not cands:
            continue
        r = cands[-1]
        if C[j] < L[r] and C[j] < AH:
            mss, ref = j, r
            break
    if mss is None:
        return None
    best = None
    for k in range(max(ext + 1, 2), min(mss + 3, n)):
        top, bot = L[k - 2], H[k]
        if top - bot >= min_fvg * pip:
            if best is None or (top - bot) >= (best[1] - best[2]):
                best = (k, top, bot)
    if best is None:
        return None
    k, top, bot = best
    return dict(ext=ext, ext_price=float(H[ext]), mss=mss, mss_level=float(L[ref]),
                fvg_k=k, fvg_top=float(top), fvg_bot=float(bot),
                fvg_time=df.index[k], ext_time=df.index[ext])


def find_setup1_candidate(name, cfg, closed, full, asia, now, d1_info, balance, sent_keys):
    pip = cfg["pip"]
    if not killzone_ok(now):
        return None
    asia_h, asia_l, asia_end = asia["high"], asia["low"], asia["end"]
    mid = asia["mid"]
    post = closed[closed.index >= asia_end - timedelta(hours=4)]

    for direction in ("short", "long"):
        if direction == "short":
            r = _detect_short_reversal(post, asia_end, asia_h, asia_l, pip, MIN_FVG_PIPS[name])
            if not r:
                continue
            ext = r["ext_price"]
            top, bot = r["fvg_top"], r["fvg_bot"]
            tp = asia_l
            entry = (top + bot) / 2
            sl = ext + SWEEP_SL_BUFFER_PIPS * pip
        else:
            m = _detect_short_reversal(mirror(post), asia_end, -asia_l, -asia_h, pip, MIN_FVG_PIPS[name])
            if not m:
                continue
            r = m
            ext = -m["ext_price"]
            top, bot = -m["fvg_bot"], -m["fvg_top"]
            tp = asia_h
            entry = (top + bot) / 2
            sl = ext - SWEEP_SL_BUFFER_PIPS * pip

        key = f"S1-{name}-{direction}-{r['ext_time']:%Y%m%d%H%M}"
        if key in sent_keys:
            continue

        age = now - (r["fvg_time"] + timedelta(minutes=5))
        if age > timedelta(minutes=FRESH_MIN):
            continue

        last = float(full.c.iloc[-1])
        if (direction == "short" and (last >= sl or last <= tp)) or \
           (direction == "long" and (last <= sl or last >= tp)):
            continue

        if not htf_allows(direction, d1_info):
            log(f"{name} S1 {direction}: HTF {d1_info['state']} не разрешает")
            continue

        magnet = opposing_h1_magnet(full, direction, entry, tp, pip)
        if magnet and SKIP_ON_H1_MAGNET:
            log(f"{name} S1 {direction}: H1-магнит → SKIP")
            sent_keys.add(key)
            continue
            return dict(
            key=key, name=name, cfg=cfg, direction=direction,
            ext=ext, top=top, bot=bot, entry=entry, sl=sl, tp=tp,
            mid=mid, last=last, r=r, balance=balance,
            d1_info=d1_info, magnet=magnet,
            ext_time=r["ext_time"],
        )
    return None


def finalize_setup1(cand, dxy_closed, sent_keys):
    name = cand["name"]
    cfg = cand["cfg"]
    direction = cand["direction"]
    pip = cfg["pip"]
    
    if dxy_closed is None or dxy_closed.empty:
        log(f"{name} S1 {direction}: нет DXY → пропуск SMT")
        return False
        
    if not smt_confirms(dxy_closed, None, cand["ext"], direction, cand["ext_time"]):
        log(f"{name} S1 {direction}: SMT нет")
        return False

    last = cand["last"]
    entry = cand["entry"]
    sl = cand["sl"]
    tp = cand["tp"]
    mid = cand["mid"]
    top = cand["top"]
    bot = cand["bot"]
    ext = cand["ext"]
    
    risk = abs(entry - sl) / pip
    reward = abs(tp - entry) / pip
    side = "SHORT 🔴 " if direction == "short" else "LONG 🟢 "
    swept = "Asia High" if direction == "short" else "Asia Low"
    d1_info = cand["d1_info"]

    txt = (
        f"⚡  <b>СЕТАП №1 (разворот Азии)</b> — {name} {side}\n"
        f"Свип {swept}: {fmt(ext, pip)} → MSS на M5 → 5м FVG "
        f"{fmt(bot, pip)}–{fmt(top, pip)} ({(top-bot)/pip:.1f} п.)\n"
        f"SMT: DXY не подтвердил ✅ \n"
        f"HTF: State {d1_info['state']} (bias: {d1_info['bias']})\n"
        f"Лимитка (0.5 FVG): <b>{fmt(entry, pip)}</b>\n"
        f"SL: {fmt(sl, pip)} (~{risk:.1f} п.)\n"
        f"TP: {fmt(tp, pip)} (~{reward:.1f} п., R:R {reward/risk:.1f})\n"
        f"Midpoint Азии: {fmt(mid, pip)}\n"
        f"Цена сейчас: {fmt(last, pip)}"
        + lot_text(cfg, cand["balance"], risk)
        + "\n\n<i>⚠️  Если после входа цена закроется за Midpoint Азии против тебя — "
          "сожми SL до −5 п. от входа (Cushion SL)</i>\n"
          "<i>⚠️  Проверь новости High Impact ±20 мин вручную</i>"
    )
    
    if telegram(txt):
        sent_keys.add(cand["key"])
        log(f"отправлен {cand['key']}")
        return True
    return False


def find_setup2_candidate(name, cfg, closed, full, asia, now, d1_info, balance, sent_keys):
    pip = cfg["pip"]
    if not killzone_ok(now):
        return None
        
    asia_h = asia["high"]
    asia_l = asia["low"]
    asia_end = asia["end"]
    
    if (asia_h - asia_l) / pip < WIDE_ASIA_PIPS[name]:
        return None

    post = closed[closed.index >= asia_end]
    p0 = next((i for i in range(len(post)) if post.h.iloc[i] > asia_h or post.l.iloc[i] < asia_l), None)
    if p0 is None:
        return None
        
    b = post.iloc[p0]
    if b.h > asia_h and b.l < asia_l:
        return None
        
    if b.h > asia_h and b.c > asia_h:
        direction = "long"
    elif b.l < asia_l and b.c < asia_l:
        direction = "short"
    else:
        return None

    if not htf_allows(direction, d1_info):
        return None

    key = f"S2-{name}-{direction}-{now:%Y%m%d}"
    if key in sent_keys:
        return None

    h1 = to_h1(full, now)
    want = "up" if direction == "long" else "down"
    cands = [g for g in h1_fvgs(h1) if g["dir"] == want and g["mid_t"] >= asia_end - timedelta(hours=1) and (g["top"] - g["bot"]) / pip >= H1_MIN_FVG_PIPS]
             
    for g in reversed(cands):
        after = full[full.index >= g["end_t"]]
        if after.empty:
            continue
            
        touched = after[after.l <= g["top"]] if direction == "long" else after[after.h >= g["bot"]]
        if touched.empty:
            continue
            
        t0 = touched.index[0]
        if now - t0 > timedelta(minutes=FRESH_MIN):
            continue
            
        last = float(full.c.iloc[-1])
        entry = last
        
        if direction == "long":
            sl = asia_l - SETUP2_SL_PIPS * pip
        else:
            sl = asia_h + SETUP2_SL_PIPS * pip
            
        risk = abs(entry - sl) / pip
        if direction == "long":
            hi = full.h.max()
            tp = float(hi) if hi > entry else None
        else:
            lo = full.l.min()
            tp = float(lo) if lo < entry else None
            
        if tp is None:
            return None
            
        reward = abs(tp - entry) / pip
        if reward < 2 * risk:
            log(f"{name} S2 skip: reward {reward:.0f} < 2×risk {risk:.0f}")
            sent_keys.add(key)
            return None
            
        magnet = opposing_h1_magnet(full, direction, entry, tp, pip)
        if magnet and SKIP_ON_H1_MAGNET:
            log(f"{name} S2: H1-магнит → SKIP")
            sent_keys.add(key)
            return None

        return dict(
            key=key, name=name, cfg=cfg, direction=direction,
            entry=entry, sl=sl, tp=tp, last=last, g=g,
            asia_l=asia_l, asia_h=asia_h, balance=balance,
            d1_info=d1_info, ext_time=g["end_t"],
        )
    return None


def finalize_setup2(cand, dxy_closed, sent_keys):
    name = cand["name"]
    cfg = cand["cfg"]
    direction = cand["direction"]
    pip = cfg["pip"]
    
    if dxy_closed is None or dxy_closed.empty:
        log(f"{name} S2 {direction}: нет DXY → пропуск SMT")
        return False
        
    if not smt_confirms(dxy_closed, None, cand["entry"], direction, cand["ext_time"]):
        log(f"{name} S2 {direction}: SMT нет")
        return False

    entry = cand["entry"]
    sl = cand["sl"]
    tp = cand["tp"]
    
    risk = abs(entry - sl) / pip
    reward = abs(tp - entry) / pip
    side = "LONG 🟢 " if direction == "long" else "SHORT 🔴 "
    g = cand["g"]
    asia_l = cand["asia_l"]
    asia_h = cand["asia_h"]
    d1_info = cand["d1_info"]

    txt = (
        f"⚡  <b>СЕТАП №2 (продолжение)</b> — {name} {side}\n"
        f"Азия {fmt(asia_l, pip)}–{fmt(asia_h, pip)} ({(asia_h-asia_l)/pip:.0f} п.), "
        f"выход без свипа.\n"
        f"Цена протестировала часовой FVG {fmt(g['bot'], pip)}–{fmt(g['top'], pip)}\n"
        f"SMT: DXY подтвердил ✅ \n"
        f"HTF: State {d1_info['state']} (bias: {d1_info['bias']})\n"
        f"Вход ~<b>{fmt(entry, pip)}</b>\n"
        f"SL: {fmt(sl, pip)} (~{risk:.0f} п., за границей Азии)\n"
        f"TP (HTF-ликвидность): {fmt(tp, pip)} (~{reward:.0f} п., R:R {reward/risk:.1f})"
        + lot_text(cfg, cand["balance"], risk)
        + "\n\n<i>⚠️  Проверь новости High Impact ±20 мин вручную</i>"
    )
    
    if telegram(txt):
        sent_keys.add(cand["key"])
        log(f"отправлен {cand['key']}")
        return True
    return False
