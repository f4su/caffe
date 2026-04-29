from flask import Flask, render_template, request, redirect
import json
import os

app = Flask(__name__)

ARCHIVO = "data.json"

CONSUMOS = {
    "Enrique": "cafe",
    "Irantzu": "cafe",
    "Iñaki": "cafe",
    "JoseG": "cafe",
    "JoseS": "cafe",
    "Kike": "cafe"
}

PERSONAS = list(CONSUMOS.keys())


def load():
    if os.path.exists(ARCHIVO):
        try:
            with open(ARCHIVO, "r") as f:
                data = json.load(f)
        except:
            data = {}
    else:
        data = {}

    for p in PERSONAS:
        if p not in data:
            data[p] = {"consumido": 0, "pagado": 0}

    return data


def save(data):
    with open(ARCHIVO, "w") as f:
        json.dump(data, f, indent=4)


def balance(data, p):
    return data[p]["pagado"] - data[p]["consumido"]


def sugerir_pagador(data, asistentes):
    balances = {p: balance(data, p) for p in asistentes}
    return min(balances, key=balances.get)


@app.route("/")
def index():
    data = load()
    return render_template(
        "index.html",
        personas=PERSONAS,
        sugerido=None,
        asistentes=[],
        data=data
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
            data=data
        )

    sugerido = sugerir_pagador(data, asistentes)

    return render_template(
        "index.html",
        personas=PERSONAS,
        sugerido=sugerido,
        asistentes=asistentes,
        data=data
    )


@app.route("/registrar", methods=["POST"])
def registrar():
    data = load()

    pagador = request.form["pagador"]
    asistentes = request.form.getlist("asistentes")

    if pagador not in asistentes:
        asistentes.append(pagador)

    n = len(asistentes)

    # cada uno consume 1 café
    for a in asistentes:
        data[a]["consumido"] += 1

    # el pagador paga por todos menos él
    data[pagador]["pagado"] += (n - 1)

    save(data)

    return redirect("/")


# 🔧 NUEVA RUTA PARA AJUSTAR
@app.route("/ajustar", methods=["POST"])
def ajustar():
    data = load()

    persona = request.form["persona"]
    cantidad = int(request.form["cantidad"])

    if persona in data:
        data[persona]["pagado"] -= cantidad

        # evitar negativos
        if data[persona]["pagado"] < 0:
            data[persona]["pagado"] = 0

    save(data)

    return redirect("/")
