from flask import Flask, render_template, request, redirect, flash
import random
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


@app.route("/")
def index():
    data = load()
    transactions = get_transactions()
    events = get_events()

    return render_template(
        "index.html",
        personas=PERSONAS,
        sugerido=None,
        asistentes=[],
        data=data,
        transactions=transactions,
        events=events   # 🔥 FIX CLAVE
    )


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
            events=get_events()
        )

    sugerido = sugerir_pagador(data, asistentes)

    return render_template(
        "index.html",
        personas=PERSONAS,
        sugerido=sugerido,
        asistentes=asistentes,
        data=data,
        transactions=get_transactions(),
        events=get_events()
    )


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

    add_event(
        "ok",
        f"{pagador} pagó {cantidad} cafés a {', '.join([a for a in asistentes if a != pagador])}"
    )

    flash(f"☕ Café registrado: {pagador} pagó {cantidad} cafés")

    return redirect("/")


@app.route("/undo", methods=["POST"])
def undo():
    data = load()

    tx = delete_last_transaction()

    if tx:
        data = revert_transaction(data, tx)
        save(data)

        add_event(
            "undo",
            f"Cancelado último café de {tx['pagador']} ({tx['cantidad']} cafés)"
        )

        flash(f"❌ Último café cancelado: {tx['pagador']}")

    return redirect("/")
