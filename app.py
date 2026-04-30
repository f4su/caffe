from flask import Flask, render_template, request, redirect, flash
import random
from db import (
    init_db,
    get_data,
    save_data,
    add_transaction,
    get_transactions,
    delete_last_transaction,
    revert_transaction
)

app = Flask(__name__)

# 🔐 necesario para flash messages
app.secret_key = "cafe_secret_key"

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


# =========================
# 🔄 CARGAR DATOS
# =========================
def load():
    data = get_data() or {}

    for p in PERSONAS:
        if p not in data:
            data[p] = {"consumido": 0, "pagado": 0}

    return data


# =========================
# 💾 GUARDAR DATOS
# =========================
def save(data):
    save_data(data)


def balance(data, p):
    return data[p]["pagado"] - data[p]["consumido"]


# =========================
# 🔥 SUGERENCIA
# =========================
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

    return render_template(
        "index.html",
        personas=PERSONAS,
        sugerido=None,
        asistentes=[],
        data=data,
        transactions=transactions
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

    # actualizar consumos
    for a in asistentes:
        if a in data:
            data[a]["consumido"] += 1

    # actualizar pagos
    if pagador in data:
        data[pagador]["pagado"] += cantidad

    save(data)

    # guardar transacción
    add_transaction(pagador, asistentes, cantidad)

    return redirect("/")


# =========================
# ❌ UNDO ÚLTIMO LOG
# =========================
@app.route("/undo", methods=["POST"])
def undo():
    data = load()

    tx = delete_last_transaction()

    if tx:
        data = revert_transaction(data, tx)
        save(data)

        # 🔔 mensaje visible en UI
        flash(f"Se ha deshecho el último pago: {tx['pagador']} pagó {tx['cantidad']} cafés")

    return redirect("/")
