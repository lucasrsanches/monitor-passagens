"""Roda uma coleta: busca preços, grava no histórico, detecta pechinchas e avisa no Telegram."""
import sys
from datetime import datetime, timezone

import config
import detector
import store
import telegram
from sources import bus, buser, flights

ORIGIN_NAMES = {"SAO": "São Paulo", "VCP": "Campinas (VCP)"}


def main():
    db = store.connect()
    telegram.diagnose(db)
    rows, failures = [], []
    seen_at = store.now_iso()
    for name, fetch in (("voos", flights.fetch), ("Buser", lambda: buser.fetch(db)),
                        ("ClickBus", lambda: bus.fetch(db))):
        try:
            got = fetch()
            store.add_obs(db, got, seen_at)   # grava já, pra não perder se a próxima fonte travar
            rows += got
        except Exception as e:  # noqa: BLE001
            failures.append(f"{name}: {e}")
            print(f"[erro] {name}: {e}")

    deals, total = detector.find_deals(db, rows, seen_at) if rows else ([], 0)
    print(f"[monitor] {len(rows)} preços, {total} pechinchas, enviando {len(deals)}")

    for d in deals:
        dest_name = config.BR_DESTINATIONS.get(d["dest"], d["dest"])
        origin_name = ORIGIN_NAMES.get(d["origin"], d["origin"])
        if telegram.send(db, telegram.format_deal(d, dest_name, origin_name)):
            store.save_alert(db, d["key"], d["price"])
    if total > len(deals):
        telegram.send(db, f"(+{total - len(deals)} outras pechinchas menores nesta rodada)")

    # aviso de saúde: falha de coleta avisa no máximo 1x por dia; status semanal às segundas
    today = datetime.now(timezone.utc).date().isoformat()
    if failures and store.kv_get(db, "last_failure_msg") != today:
        telegram.send(db, "⚠️ Monitor de passagens com problema:\n" + "\n".join(failures))
        store.kv_set(db, "last_failure_msg", today)
    week = datetime.now(timezone.utc).strftime("%G-W%V")
    if store.kv_get(db, "last_weekly") != week:
        n = db.execute("SELECT COUNT(*) FROM obs").fetchone()[0]
        routes = db.execute("SELECT COUNT(DISTINCT mode||origin||dest) FROM obs").fetchone()[0]
        if telegram.send(db, f"✅ Monitor ativo. Histórico: {n:,} preços em {routes} rotas.".replace(",", ".")):
            store.kv_set(db, "last_weekly", week)

    store.prune(db)
    db.execute("VACUUM")
    db.close()
    return 1 if failures and not rows else 0


if __name__ == "__main__":
    sys.exit(main())
