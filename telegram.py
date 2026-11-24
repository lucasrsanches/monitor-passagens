"""Envio de alertas pelo bot do Telegram.

Precisa só do segredo TELEGRAM_BOT_TOKEN. O chat é descoberto sozinho: basta mandar /start
para o bot uma vez. O id do chat fica salvo no banco (não é segredo).
"""
import os
from datetime import date

import requests

import store

API = "https://api.telegram.org/bot{token}/{method}"
DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _call(method, **params):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return None
    r = requests.post(API.format(token=token, method=method), json=params, timeout=30)
    r.raise_for_status()
    return r.json().get("result")


def chat_id(db):
    cid = os.environ.get("TELEGRAM_CHAT_ID") or store.kv_get(db, "telegram_chat_id")
    if cid:
        return cid
    for upd in _call("getUpdates") or []:
        chat = (upd.get("message") or {}).get("chat") or {}
        if chat.get("type") == "private":
            store.kv_set(db, "telegram_chat_id", chat["id"])
            return chat["id"]
    return None


def send(db, text):
    cid = chat_id(db)
    if not cid:
        print("[telegram] sem chat ainda — mande /start para o bot. Mensagem não enviada:\n" + text)
        return False
    _call("sendMessage", chat_id=cid, text=text, parse_mode="HTML", disable_web_page_preview=True)
    return True


def brl(v):
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def fmt_date(iso):
    d = date.fromisoformat(iso)
    return f"{DIAS[d.weekday()]} {d.day:02d}/{MESES[d.month - 1]}"


def format_deal(d, dest_name, origin_name):
    icon = "✈️" if d["mode"] == "aviao" else "🚌"
    off = round((1 - d["ratio"]) * 100)
    tag = "🔥 MENOR PREÇO JÁ VISTO" if d["is_record"] else "📉 perto do menor já visto"
    if d["ratio"] <= 0.4:
        tag = "🚨 POSSÍVEL ERRO DE TARIFA"
    hora = f" {d['dep_time']}" if d.get("dep_time") else ""
    extra = f"\n{d['carrier']}" + (f" · {d['info']}" if d.get("info") else "") if d.get("carrier") else ""
    link = f'\n<a href="{d["link"]}">Abrir busca</a>' if d.get("link") else ""
    return (
        f"{icon} <b>{origin_name} → {dest_name}</b>\n"
        f"{fmt_date(d['dep_date'])}{hora} · <b>{brl(d['price'])}</b> (−{off}% do normal)\n"
        f"Normal: {brl(d['median'])} · Menor anterior: {brl(d['record'])} · {d['samples']} preços no histórico\n"
        f"{tag}{extra}{link}"
    )
