from flask import Flask, render_template, request, redirect
import json
import os

app = Flask(__name__)

ARCHIVO = "data.json"

CONSUMOS = {
    "JoseG": "cafe_solo",
    "Irantxu": "sandwich",
    "JoseS": "cafe_con_leche",
    "Kike": "cafe_con_leche",
    "Enrique": "cafe_con_leche",
    "Iñaki": "cafe_con_leche"
}

PRECIOS = {
    "cafe_solo": 1.20,
    "cafe_con_leche": 1.50,
    "sandwich": 3.00
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
            data[p] = {"debe": 0.0, "pagado": 0.0}

    return data


def save(data):
    with open(ARCHIVO, "w") as f:
        json.dump(data, f, indent=4)


def coste(persona):
    return PRECIOS[CONSUMOS[persona]]


def sugerir_pagador(data, asistentes):
    # quien ha pagado más vs lo que debe dentro del grupo
    balances = {}

    for p in asistentes:
        balances[p] = data[p]["pagado"] - data[p]["debe"]

    # el que más debe (más negativo) es el sugerido pagador
    return min(balances, key=balances.get)


@app.route("/")
def index():
    data = load()
    sugerido = sugerir_pagador(data, PERSONAS)

    return render_template(
        "index.html",
        personas=PERSONAS,
        data=data,
        sugerido=sugerido
    )


@app.route("/registrar", methods=["POST"])
def registrar():
    data = load()

    pagador = request.form["pagador"]
    asistentes = request.form.getlist("asistentes")

    if not asistentes:
        return redirect("/")

    if pagador not in asistentes:
        asistentes.append(pagador)

    total = 0

    for a in asistentes:
        total += coste(a)

    # pagador paga todo menos lo suyo
    data[pagador]["pagado"] += (total - coste(pagador))

    # los demás deben su consumo
    for a in asistentes:
        if a != pagador:
            data[a]["debe"] += coste(a)

    save(data)

    return redirect("/")
