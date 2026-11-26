"""Histórico de preços em SQLite (data/prices.db, versionado no repositório)."""
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("PRICES_DB") or Path(__file__).parent / "data" / "prices.db")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(path=DB_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS obs (
            seen_at   TEXT NOT NULL,      -- quando o preço foi visto (UTC)
            mode      TEXT NOT NULL,      -- 'aviao' | 'onibus'
            origin    TEXT NOT NULL,
            dest      TEXT NOT NULL,
            dep_date  TEXT NOT NULL,      -- AAAA-MM-DD
            dep_time  TEXT,
            price     REAL NOT NULL,
            carrier   TEXT,
            info      TEXT,               -- escalas, classe, etc.
            link      TEXT
        );
        CREATE INDEX IF NOT EXISTS obs_route ON obs(mode, origin, dest, seen_at);
        CREATE TABLE IF NOT EXISTS alerts (
            key      TEXT PRIMARY KEY,    -- modo|origem|destino|data
            price    REAL NOT NULL,
            sent_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);
        """
    )
    cols = {c[1] for c in db.execute("PRAGMA table_info(obs)")}
    for col in ("ret_date", "link2"):          # colunas novas (ida e volta)
        if col not in cols:
            db.execute(f"ALTER TABLE obs ADD COLUMN {col} TEXT")
    db.commit()
    return db


def add_obs(db, rows, seen_at=None):
    seen_at = seen_at or now_iso()
    db.executemany(
        "INSERT INTO obs (seen_at, mode, origin, dest, dep_date, dep_time, price, carrier, info, link,"
        " ret_date, link2) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [(seen_at, r["mode"], r["origin"], r["dest"], r["dep_date"], r.get("dep_time"),
          float(r["price"]), r.get("carrier"), r.get("info"), r.get("link"),
          r.get("ret_date"), r.get("link2")) for r in rows],
    )
    db.commit()
    return seen_at


def route_prices(db, mode, origin, dest, days, exclude_seen_at=None):
    """Preços distintos (data de partida, preço) já vistos na rota dentro da janela."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = ("SELECT DISTINCT dep_date, price FROM obs WHERE mode=? AND origin=? AND dest=? "
         "AND seen_at>=?")
    args = [mode, origin, dest, since]
    if exclude_seen_at:
        q += " AND seen_at<>?"
        args.append(exclude_seen_at)
    return [p for _, p in db.execute(q, args)]


def latest_prices(db, mode, hours):
    """Último preço conhecido de cada (origem, destino, data) visto nas últimas N horas."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = ("SELECT origin, dest, dep_date, price, carrier, info, link, dep_time, MAX(seen_at) "
         "FROM obs WHERE mode=? AND seen_at>=? GROUP BY origin, dest, dep_date")
    keys = ("origin", "dest", "dep_date", "price", "carrier", "info", "link", "dep_time")
    return [dict(zip(keys, r[:8])) for r in db.execute(q, (mode, since))]


def last_alert(db, key):
    return db.execute("SELECT price, sent_at FROM alerts WHERE key=?", (key,)).fetchone()


def save_alert(db, key, price):
    db.execute("INSERT OR REPLACE INTO alerts VALUES (?,?,?)", (key, price, now_iso()))
    db.commit()


def kv_get(db, k, default=None):
    row = db.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
    return row[0] if row else default


def kv_set(db, k, v):
    db.execute("INSERT OR REPLACE INTO kv VALUES (?,?)", (k, str(v)))
    db.commit()


def prune(db, keep_days=400):
    """Apaga observações muito antigas e partidas que já passaram há mais de 1 ano."""
    cut = (datetime.now(timezone.utc) - timedelta(days=keep_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    db.execute("DELETE FROM obs WHERE seen_at<?", (cut,))
    db.commit()
