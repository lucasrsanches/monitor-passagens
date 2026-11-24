"""Preços de ônibus pela página pública de busca da ClickBus.

Abre a página de busca num navegador automático (Playwright), como um visitante comum, e lê
os resultados que a própria página carrega. Imagens, fontes e rastreadores são bloqueados pra
ficar leve. Cada execução consulta só uma parte das datas (rodízio), então o site recebe poucas
visitas por rodada.
"""
import re
import time
from datetime import date, timedelta

import config
import store

SEARCH = "https://www.clickbus.com.br/onibus/{o}/{d}?departureDate={dt}"
BLOCK = re.compile(r"\.(png|jpe?g|webp|gif|svg|woff2?|ttf|mp4)(\?|$)|google|doubleclick|hotjar|"
                   r"useinsider|amplitude|visualwebsiteoptimizer|crmback|facebook|tiktok")

# nome da rodoviária de embarque (como a ClickBus escreve) -> rótulo curto
TERMINALS = [("tiet", "Tietê"), ("barra funda", "Barra Funda"), ("jabaquara", "Jabaquara"),
             ("santo andr", "Santo André"), ("bernardo", "São Bernardo")]


def _terminal(name):
    low = (name or "").lower()
    for needle, label in TERMINALS:
        if needle in low:
            return label
    return None


def _hours(s):
    m = re.match(r"\s*(\d+)h\s*(\d+)?", s or "")
    return int(m.group(1)) + int(m.group(2) or 0) / 60 if m else 99


def _plan(run_no):
    """Quais (rota, data) consultar nesta execução. Prioridade 1 é olhada com mais frequência."""
    today = date.today()
    jobs = []
    for route in config.BUS_ROUTES:
        o_slug, d_slug, dest, prio = route
        every = config.BUS_EVERY_N_RUNS[prio]
        for i in range(1, config.BUS_DAYS_AHEAD + 1):
            if (i + run_no) % every == 0:
                jobs.append((o_slug, d_slug, dest, (today + timedelta(days=i)).isoformat()))
    return jobs


def _rows_from(payload, dest, dep, url):
    trips = [t for t in payload.get("trips") or [] if t.get("price")]
    if not trips:
        return []
    fastest = min(_hours(t["duration"]["hours"]) for t in trips)
    best = {}
    for t in trips:
        h = _hours(t["duration"]["hours"])
        if h > fastest * 1.5 + 1 or h > config.BUS_MAX_HOURS.get(dest, config.BUS_MAX_HOURS["*"]):
            continue   # descarta conexões absurdas (ex.: Santo André -> Peruíbe em 20h)
        first = t["parts"][0]
        term = _terminal(first["departure"]["name"])
        if not term:
            continue
        if term not in best or t["price"] < best[term]["price"]:
            best[term] = t
    rows = []
    for term, t in best.items():
        first = t["parts"][0]
        bits = [first["serviceClass"]["name"], t["duration"]["hours"]]
        if t["type"] != "direct":
            bits.append("com conexão")
        if t.get("originalPrice") and t["originalPrice"] > t["price"] + 0.5:
            bits.append(f"de R$ {t['originalPrice']:.0f}")
        rows.append({
            "mode": "onibus", "origin": term, "dest": dest, "dep_date": dep,
            "dep_time": first["departure"]["time"][:5], "price": float(t["price"]),
            "carrier": first["travelCompany"]["name"], "info": " · ".join(bits), "link": url,
        })
    return rows


def fetch(db=None):
    if not config.BUS_ENABLED:
        return []
    from playwright.sync_api import sync_playwright

    run_no = int(store.kv_get(db, "bus_run", 0)) if db else 0
    jobs = _plan(run_no)[: config.BUS_MAX_PAGES_PER_RUN]
    rows, fails, t0 = [], 0, time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="pt-BR")
        page.route("**/*", lambda r: r.abort() if BLOCK.search(r.request.url) else r.continue_())
        for o_slug, d_slug, dest, dep in jobs:
            url = SEARCH.format(o=o_slug, d=d_slug, dt=dep)
            try:
                with page.expect_response(lambda r: "/api/v6/trips" in r.url, timeout=35000) as info:
                    page.goto(url, wait_until="domcontentloaded")
                rows += _rows_from(info.value.json(), dest, dep, url)
            except Exception as e:  # noqa: BLE001
                fails += 1
                print(f"[ônibus] falhou {o_slug}->{d_slug} {dep}: {str(e)[:80]}")
            time.sleep(config.BUS_PAUSE_SECONDS)
        browser.close()
    if db:
        store.kv_set(db, "bus_run", run_no + 1)
    print(f"[ônibus] {len(jobs)} buscas, {fails} falhas, {len(rows)} preços em {time.time() - t0:.0f}s")
    if jobs and fails > len(jobs) * 0.5 and not rows:
        raise RuntimeError(f"ClickBus: {fails}/{len(jobs)} buscas falharam (bloqueio ou mudança no site?)")
    return rows
