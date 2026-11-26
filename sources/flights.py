"""Preços de voo pela API oficial de dados da Travelpayouts/Aviasales (gratuita, precisa de token).

Os preços vêm do cache de buscas reais feitas por usuários (não é a tarifa ao vivo), então
servem muito bem para montar histórico e achar anomalias. Antes de comprar, confira o link.
"""
import os
from datetime import date
from urllib.parse import quote

import requests

import config

BASE = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"


def _months_ahead(n):
    d = date.today().replace(day=1)
    for _ in range(n):
        yield d.strftime("%Y-%m")
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def google_flights_link(origin, dest, dep):
    q = quote(f"Flights from {origin} to {dest} on {dep} one way")
    return f"https://www.google.com/travel/flights?q={q}&hl=pt-BR&curr=BRL"


def _get(params, token):
    r = requests.get(BASE, params={**params, "token": token}, timeout=40)
    if r.status_code == 401:
        raise RuntimeError("Token da Travelpayouts inválido (401)")
    r.raise_for_status()
    body = r.json()
    if not body.get("success", True):
        raise RuntimeError(f"Travelpayouts: {body.get('error')}")
    return body.get("data") or []


def _row(t, origin, round_trip):
    """Converte um item da API numa linha do histórico (ou None se não interessa)."""
    dest = (t.get("destination") or "").upper()
    airport = (t.get("origin_airport") or "").upper()
    if dest not in config.FLIGHT_DESTINATIONS or not t.get("price"):
        return None
    if airport not in config.FLIGHT_AIRPORTS:      # só Guarulhos e Congonhas
        return None
    dep_at = t.get("departure_at") or ""
    dep, ret = dep_at[:10], (t.get("return_at") or "")[:10]
    dest_airport = t.get("destination_airport") or dest
    transfers = t.get("transfers")
    stops = ("direto" if transfers == 0 else f"{transfers} escala(s)") if transfers is not None else ""
    row = {
        "mode": "aviao", "origin": origin, "dest": dest, "dep_date": dep,
        "dep_time": dep_at[11:16] or None, "price": float(t["price"]), "carrier": t.get("airline"),
        "info": " · ".join(x for x in (f"saindo de {airport}", stops) if x),
        "link": google_flights_link(airport, dest_airport, dep),
    }
    if round_trip:
        if not ret:
            return None
        nights = (date.fromisoformat(ret) - date.fromisoformat(dep)).days
        if not config.TRIP_MIN_NIGHTS <= nights <= config.TRIP_MAX_NIGHTS:
            return None
        q = quote(f"Flights from {airport} to {dest_airport} on {dep} returning {ret}")
        row.update(mode="aviao_iv", ret_date=ret,
                   link=f"https://www.google.com/travel/flights?q={q}&hl=pt-BR&curr=BRL")
    return row


def fetch():
    token = os.environ.get("TRAVELPAYOUTS_TOKEN", "").strip()
    if not token:
        print("[voos] TRAVELPAYOUTS_TOKEN ausente — pulando voos")
        return []

    rows, errors, skipped = [], 0, 0
    for one_way in ("true", "false"):            # só ida, depois ida e volta
        for origin in config.FLIGHT_ORIGINS:
            for month in _months_ahead(config.FLIGHT_MONTHS_AHEAD):
                for page in (1, 2, 3, 4, 5):   # mais páginas: agora entram internacionais
                    try:
                        data = _get({
                            "origin": origin, "departure_at": month, "one_way": one_way,
                            "currency": "brl", "market": "br", "sorting": "price",
                            "limit": 1000, "page": page,
                        }, token)
                    except Exception as e:  # noqa: BLE001
                        errors += 1
                        print(f"[voos] {origin} {month} p{page}: {e}")
                        break
                    for t in data:
                        row = _row(t, origin, one_way == "false")
                        if row:
                            rows.append(row)
                        else:
                            skipped += 1
                    if len(data) < 1000:
                        break
    n_rt = sum(r["mode"] == "aviao_iv" for r in rows)
    n_intl = sum(r["dest"] in config.INTL_DESTINATIONS for r in rows)
    print(f"[voos] internacionais: {n_intl} preços, "
          f"{len({r['dest'] for r in rows if r['dest'] in config.INTL_DESTINATIONS})} destinos")
    print(f"[voos] {len(rows) - n_rt} só ida + {n_rt} ida e volta (GRU/CGH), "
          f"{skipped} descartados, {errors} erros")
    if errors and not rows:
        raise RuntimeError("Nenhum preço de voo coletado — verificar token/API")
    return rows
