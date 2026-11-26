"""Decide o que é pechincha de verdade comparando com o histórico da própria rota."""
from datetime import date, datetime, timezone
from statistics import median

import config
import store


def _days_ahead(dep_date):
    try:
        return (date.fromisoformat(dep_date) - datetime.now(timezone.utc).date()).days
    except ValueError:
        return -1


def find_deals(db, rows, seen_at):
    # menor preço de cada viagem (modo, origem, destino, data) nesta execução
    best = {}
    for r in rows:
        if r["mode"] in config.NO_SINGLE_ALERT:
            continue
        k = (r["mode"], r["origin"], r["dest"], r["dep_date"])
        if k not in best or r["price"] < best[k]["price"]:
            best[k] = r

    stats_cache, deals = {}, []
    for (mode, origin, dest, dep), r in best.items():
        if _days_ahead(dep) < config.MIN_DAYS_AHEAD:
            continue
        rk = (mode, origin, dest)
        if rk not in stats_cache:
            hist = store.route_prices(db, mode, origin, dest, config.HISTORY_DAYS, exclude_seen_at=seen_at)
            stats_cache[rk] = (len(hist), median(hist), min(hist)) if hist else (0, None, None)
        n, med, rec = stats_cache[rk]
        if n < config.MIN_SAMPLES:
            continue

        price = r["price"]
        ratio = price / med
        is_record = price <= rec * config.NEAR_RECORD
        if not ((is_record and ratio <= config.MAX_RATIO_VS_MEDIAN) or ratio <= config.EXTREME_RATIO):
            continue

        key = f"{mode}|{origin}|{dest}|{dep}" + (f"|{r['ret_date']}" if r.get("ret_date") else "")
        prev = store.last_alert(db, key)
        if prev:
            prev_price, prev_at = prev
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(prev_at.replace("Z", "+00:00"))).days
            if age < config.REALERT_DAYS and price > prev_price * config.REALERT_DROP:
                continue

        deals.append({**r, "key": key, "median": med, "record": rec, "samples": n,
                      "ratio": ratio, "is_record": price < rec})

    deals.sort(key=lambda d: d["ratio"])
    return deals[: config.MAX_ALERTS_PER_RUN], len(deals)
