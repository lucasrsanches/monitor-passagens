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


def fetch():
    token = os.environ.get("TRAVELPAYOUTS_TOKEN", "").strip()
    if not token:
        print("[voos] TRAVELPAYOUTS_TOKEN ausente — pulando voos")
        return []

    rows, errors = [], 0
    for origin in config.FLIGHT_ORIGINS:
        for month in _months_ahead(config.FLIGHT_MONTHS_AHEAD):
            for page in (1, 2, 3):
                try:
                    data = _get({
                        "origin": origin, "departure_at": month, "one_way": "true",
                        "currency": "brl", "market": "br", "sorting": "price",
                        "limit": 1000, "page": page,
                    }, token)
                except Exception as e:  # noqa: BLE001
                    errors += 1
                    print(f"[voos] {origin} {month} p{page}: {e}")
                    break
                for t in data:
                    dest = (t.get("destination") or "").upper()
                    if dest not in config.BR_DESTINATIONS or not t.get("price"):
                        continue
                    dep_at = t.get("departure_at") or ""
                    dep = dep_at[:10]
                    transfers = t.get("transfers")
                    rows.append({
                        "mode": "aviao", "origin": origin, "dest": dest, "dep_date": dep,
                        "dep_time": dep_at[11:16] or None, "price": float(t["price"]),
                        "carrier": t.get("airline"),
                        "info": ("direto" if transfers == 0 else f"{transfers} escala(s)") if transfers is not None else None,
                        "link": google_flights_link(t.get("origin_airport") or origin, t.get("destination_airport") or dest, dep),
                    })
                if len(data) < 1000:
                    break
    print(f"[voos] {len(rows)} preços nacionais coletados ({errors} erros)")
    if errors and not rows:
        raise RuntimeError("Nenhum preço de voo coletado — verificar token/API")
    return rows
