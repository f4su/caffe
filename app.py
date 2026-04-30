from flask import Flask, render_template, request, redirect
import random
from db import init_db, get_data, save_data, add_transaction, get_transactions

app = Flask(__name__)

# inicializar DB
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


# 🔄 cargar datos desde PostgreSQL
def load():
    data = get_data() or {}

    # asegurar estructura
    for p in PERSONAS:
        if p not in data:
            data[p] = {"consumido": 0, "pagado": 0}

    return data


# 💾 guardar datos en PostgreSQL
def save(data):
    save_data(data)


def balance(data, p):
    return data[p]["pagado"] - data[p]["consumido"]


# 🔥 LÓGICA MEJORADA DE SUGERENCIA
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

    return render_template(
        "index.html",
        personas=PERSONAS,
        sugerido=None,
        asistentes=[],
        data=data,
        transactions=transactions
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
            transactions=get_transactions()
        )

    sugerido = sugerir_pagador(data, asistentes)

    return render_template(
        "index.html",
        personas=PERSONAS,
        sugerido=sugerido,
        asistentes=asistentes,
        data=data,
        transactions=get_transactions()
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

    # actualizar lógica de cafés
    for a in asistentes:
        data[a]["consumido"] += 1

    data[pagador]["pagado"] += cantidad

    save(data)

    # 🧾 guardar transacción
    add_transaction(pagador, asistentes, cantidad)

    return redirect("/")
