"""Monta combos de ida e volta de ônibus a partir dos preços já coletados.

Para cada destino e data de ida, junta a ida mais barata (qualquer origem: SP ou ABC,
qualquer site) com a volta mais barata entre TRIP_MIN_NIGHTS e TRIP_MAX_NIGHTS depois.
Os combos viram linhas "onibus_iv" no histórico, comparadas como qualquer outra rota.
"""
from collections import defaultdict
from datetime import date, timedelta

import config
import store


def _cheapest_by_day(rows, city_key):
    best = defaultdict(dict)
    for r in rows:
        city, day = r[city_key], r["dep_date"]
        if day not in best[city] or r["price"] < best[city][day]["price"]:
            best[city][day] = r
    return best


def _leg(r, who):
    parts = [f"{who} {r['dep_time'] or ''}".strip(), r["carrier"] or ""]
    return " ".join(p for p in parts if p) + f" R$ {r['price']:.0f}"


def build(db):
    hours = config.COMBO_LOOKBACK_HOURS
    out = _cheapest_by_day(store.latest_prices(db, "onibus", hours), "dest")
    back = _cheapest_by_day(store.latest_prices(db, "onibus_volta", hours), "origin")
    today = date.today().isoformat()
    rows = []
    for city, outs in out.items():
        rets = back.get(city)
        if not rets:
            continue
        for d1, o in outs.items():
            if d1 <= today:
                continue
            start = date.fromisoformat(d1)
            options = [rets[d2] for n in range(config.TRIP_MIN_NIGHTS, config.TRIP_MAX_NIGHTS + 1)
                       if (d2 := (start + timedelta(days=n)).isoformat()) in rets]
            if not options:
                continue
            r = min(options, key=lambda x: x["price"])
            rows.append({
                "mode": "onibus_iv", "origin": "SP/ABC", "dest": city, "dep_date": d1,
                "ret_date": r["dep_date"], "price": round(o["price"] + r["price"], 2),
                "carrier": None,
                "info": f"ida: saindo de {o['origin']}, {_leg(o, '')} · volta: {_leg(r, '')}",
                "link": o["link"], "link2": r["link"],
            })
    return rows
