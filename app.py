from flask import Flask, render_template, request, redirect, flash, Response
import random
import json
import io
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
    "Iñaki":   "cafe",
    "Leire":   "cafe",
    "JoseG":   "cafe",
    "JoseS":   "cafe",
    "Kike":    "cafe"
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
    return render_template(
        "index.html",
        personas=PERSONAS,
        sugerido=None,
        asistentes=[],
        data=data,
        transactions=get_transactions(),
        events=get_events(limit=7)
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

# =========================
# 💾 EXPORTAR BASE DE DATOS
# =========================

@app.route("/export")
def export_db():
    data = get_data()
    transactions = get_transactions(limit=999999)
    events = get_events(limit=999999)

    output = io.StringIO()

    output.write("-- =============================================\n")
    output.write("-- CAFFE DB EXPORT\n")
    output.write(f"-- Generado: {datetime.now().isoformat()}\n")
    output.write("-- =============================================\n\n")

    # Resumen legible
    output.write("-- ESTADO ACTUAL (consumido / pagado por persona)\n")
    for persona, vals in data.items():
        output.write(f"--   {persona}: consumido={vals.get('consumido', 0)}, pagado={vals.get('pagado', 0)}\n")

    output.write("\n-- TRANSACCIONES\n")
    for tx in transactions:
        asistentes_str = ", ".join(tx["asistentes"])
        output.write(f"--   {tx['pagador']} pagó {tx['cantidad']} cafés a: {asistentes_str}\n")

    output.write("\n-- EVENTOS\n")
    for ev in events:
        output.write(f"--   [{ev['type']}] {ev['message']}\n")

    # SQL para reimportar
    output.write("\n\n-- =============================================\n")
    output.write("-- SQL PARA REIMPORTAR EN NUEVA BASE DE DATOS\n")
    output.write("-- =============================================\n\n")

    output.write("-- Crear tablas si no existen\n")
    output.write("""CREATE TABLE IF NOT EXISTS app_data (
    id SERIAL PRIMARY KEY,
    data JSONB
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    pagador TEXT NOT NULL,
    asistentes TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);\n\n""")

    # app_data
    output.write("-- Datos de estado\n")
    output.write("DELETE FROM app_data;\n")
    data_json = json.dumps(data).replace("'", "''")
    output.write(f"INSERT INTO app_data (data) VALUES ('{data_json}');\n\n")

    # transactions
    output.write("-- Transacciones\n")
    output.write("DELETE FROM transactions;\n")
    for tx in transactions:
        pagador = tx['pagador'].replace("'", "''")
        asistentes_str = ",".join(tx["asistentes"]).replace("'", "''")
        output.write(
            f"INSERT INTO transactions (pagador, asistentes, cantidad) "
            f"VALUES ('{pagador}', '{asistentes_str}', {tx['cantidad']});\n"
        )

    # events
    output.write("\n-- Eventos\n")
    output.write("DELETE FROM events;\n")
    for ev in events:
        etype = ev['type'].replace("'", "''")
        msg = ev['message'].replace("'", "''")
        output.write(
            f"INSERT INTO events (type, message) "
            f"VALUES ('{etype}', '{msg}');\n"
        )

    content = output.getvalue()
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=caffe_export.sql"}
    )
