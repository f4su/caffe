from flask import Flask, render_template, request, redirect, flash
import random
from datetime import datetime
from db import (
    init_db,
    get_data,
    save_data,
    add_transaction,
    get_transactions,
    delete_last_transaction,
    revert_transaction,
    add_event,
    get_events
)

app = Flask(__name__)

app.secret_key = "cafe_secret_key"

init_db()

CONSUMOS = {
    "Enrique": "cafe",
    "Irantzu": "cafe",
    "Iñaki": "cafe",
    "Leire": "cafe",
    "JoseG": "cafe",
    "JoseS": "cafe",
    "Kike": "cafe"
}

PERSONAS = list(CONSUMOS.keys())


# =========================
# 📅 FECHA FORMATEADA
# =========================
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

DIAS = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"
]


def fecha_formateada():
    now = datetime.now()
    return f"{DIAS[now.weekday()]}, {now.day} {MESES[now.month - 1]}"


# =========================
# 🔄 LOAD
# =========================
def load():
    data = get_data() or {}

    for p in PERSONAS:
        if p not in data:
            data[p] = {"consumido": 0, "pagado": 0}

    return data


def save(data):
    save_data(data)


def balance(data, p):
    return data[p]["pagado"] - data[p]["consumido"]


def sugerir_pagador(data, asistentes):
    balances = {p: balance(data, p) for p in asistentes}

    min_balance = min(balances.values())
    candidatos = [p for p in asistentes if balances[p] == min_balance]

    if len(candidatos) == 1:
        return candidatos[0]

    min_pagado = min(data[p]["pagado"] for p in candidatos)
    candidatos = [p for p in candidatos if data[p]["pagado"] == min_pagado]

    return random.choice(candidatos)


# =========================
# 🌐 HOME
# =========================
@app.route("/")
def index():
    data = load()

    transactions = get_transactions()
    events = get_events(limit=7)   # 🔥 SOLO ÚLTIMOS 7

    return render_template(
        "index.html",
        personas=PERSONAS,
        sugerido=None,
        asistentes=[],
        data=data,
        transactions=transactions,
        events=events
    )


# =========================
# 👀 PREVIEW
# =========================
@app.route("/preview", methods=["POST"])
def preview():
    data = load()
    asistentes = request.form.getlist("asistentes")

    if not asistentes:
        return render_template(
            "index.html",
            personas=PERSONAS,
            sugerido=None,
            asistentes=[],
            data=data,
            transactions=get_transactions(),
            events=get_events(limit=7)
        )

    sugerido = sugerir_pagador(data, asistentes)

    return render_template(
        "index.html",
        personas=PERSONAS,
        sugerido=sugerido,
        asistentes=asistentes,
        data=data,
        transactions=get_transactions(),
        events=get_events(limit=7)
    )


# =========================
# ☕ REGISTRAR CAFÉ
# =========================
@app.route("/registrar", methods=["POST"])
def registrar():
    data = load()

    pagador = request.form["pagador"]
    asistentes = request.form.getlist("asistentes")

    if pagador not in asistentes:
        asistentes.append(pagador)

    n = len(asistentes)
    cantidad = n - 1

    for a in asistentes:
        if a in data:
            data[a]["consumido"] += 1

    if pagador in data:
        data[pagador]["pagado"] += cantidad

    save(data)
    add_transaction(pagador, asistentes, cantidad)

    fecha = fecha_formateada()
    asistentes_sin_pagador = [a for a in asistentes if a != pagador]

    add_event(
        "ok",
        f"{fecha}: {pagador} pagó {cantidad} cafés a: {', '.join(asistentes_sin_pagador)}"
    )

    flash(f"☕ Café registrado: {pagador} pagó {cantidad} cafés")

    return redirect("/")


# =========================
# ❌ UNDO
# =========================
@app.route("/undo", methods=["POST"])
def undo():
    data = load()

    tx = delete_last_transaction()

    if tx:
        data = revert_transaction(data, tx)
        save(data)

        fecha = fecha_formateada()

        add_event(
            "undo",
            f"{fecha}: cancelado café de {tx['pagador']} ({tx['cantidad']} cafés)"
        )

        flash(f"❌ Último café cancelado: {tx['pagador']}")

    return redirect("/")
