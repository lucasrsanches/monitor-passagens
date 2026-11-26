"""Preços de ônibus da Buser pela página pública de busca.

Cada página da Buser já traz um calendário com o menor preço de 8 dias seguidos, então poucas
visitas cobrem os próximos 60 dias. A Buser agrupa por cidade (não por rodoviária).
"""
import re
import time
from datetime import date, timedelta

import config
import store

SEARCH = "https://www.buser.com.br/onibus/{o}/{d}?ida={dt}"
BLOCK = re.compile(r"\.(png|jpe?g|webp|gif|svg|woff2?|ttf|mp4)(\?|$)|google|doubleclick|facebook|"
                   r"hotjar|tiktok|clarity")
ORIGIN_LABEL = {"sao-paulo-sp": "São Paulo (Buser)", "santo-andre-sp": "Santo André (Buser)",
                "sao-bernardo-do-campo-sp": "São Bernardo (Buser)"}
WINDOW = 8   # dias por página


def _plan(run_no):
    """Cada rota tem janelas de 8 dias; prioridade 1 vê 2 janelas por execução, as outras 1."""
    today = date.today()
    n_windows = -(-config.BUS_DAYS_AHEAD // WINDOW)
    jobs = []
    for o, d, city, prio, volta in config.BUSER_ROUTES:
        per_run = 2 if prio == 1 else 1
        for k in range(per_run):
            w = (run_no * per_run + k) % n_windows
            anchor = today + timedelta(days=3 + w * WINDOW)   # página mostra anchor-2 .. anchor+5
            jobs.append((prio, o, d, city, volta, anchor.isoformat()))
    jobs.sort(key=lambda j: j[0])
    return [j[1:] for j in jobs]


def fetch(db=None):
    if not config.BUSER_ENABLED:
        return []
    from playwright.sync_api import sync_playwright

    run_no = int(store.kv_get(db, "buser_run", 0)) if db else 0
    jobs = _plan(run_no)
    rows, fails, done, t0 = [], 0, 0, time.time()
    pause, today = config.BUSER_PAUSE_SECONDS, date.today().isoformat()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="pt-BR")
        page.route("**/*", lambda r: r.abort() if BLOCK.search(r.request.url) else r.continue_())
        for o, d, city, volta, anchor in jobs:
            if time.time() - t0 > config.BUSER_TIME_BUDGET_SECONDS:
                print(f"[buser] tempo esgotado depois de {done} buscas")
                break
            done += 1
            url = SEARCH.format(o=o, d=d, dt=anchor)
            main = None
            try:
                with page.expect_response(lambda r: "menor-preco-por-dia" in r.url, timeout=20000) as info:
                    main = page.goto(url, wait_until="domcontentloaded")
                    if main and main.status == 429:
                        raise RuntimeError("429")
                if info.value.status != 200:
                    raise RuntimeError(f"HTTP {info.value.status}")
                got = 0
                for day in info.value.json().get("precos") or []:
                    if day.get("price") and day.get("date", "") > today:
                        rows.append({
                            "mode": "onibus_volta" if volta else "onibus",
                            "origin": city if volta else ORIGIN_LABEL.get(o, o),
                            "dest": "SP/ABC" if volta else city,
                            "dep_date": day["date"], "price": float(day["price"]), "carrier": "Buser",
                            "info": "menor preço do dia" + (f" · chega em {ORIGIN_LABEL.get(d, d)}" if volta else ""),
                            "link": SEARCH.format(o=o, d=d, dt=day["date"]),
                        })
                        got += 1
                if done <= 2:
                    print(f"[buser] {o}->{d} {anchor}: {got} dias com preço")
            except Exception as e:  # noqa: BLE001
                fails += 1
                if "429" in str(e) or (main is not None and main.status == 429):
                    pause = min(pause * 2, 60)
                    print(f"[buser] site pediu calma (429) — esperando 90s; nova pausa {pause:.0f}s")
                    time.sleep(90)
                    if fails >= 3:
                        break
                else:
                    print(f"[buser] falhou {o}->{d} {anchor}: {str(e)[:60]}")
            time.sleep(pause)
        browser.close()
    if db:
        store.kv_set(db, "buser_run", run_no + 1)
    print(f"[buser] {done} buscas, {fails} falhas, {len(rows)} preços em {time.time() - t0:.0f}s")
    if done and fails > done * 0.5 and not rows:
        raise RuntimeError(f"Buser: {fails}/{done} buscas falharam")
    return rows
