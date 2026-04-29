from flask import Flask, render_template, request, redirect
import json
import os

app = Flask(__name__)

ARCHIVO = "data.json"

CONSUMOS = {
    "Enrique": "cafe_con_leche",
    "Irantxu": "sandwich",
    "Iñaki": "cafe_con_leche",
    "JoseG": "cafe_solo",
    "JoseS": "cafe_con_leche",
    "Kike": "cafe_con_leche"
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


def coste(p):
    return PRECIOS[CONSUMOS[p]]


def sugerir_pagador(data, asistentes):
    balances = {
        p: data[p]["pagado"] - data[p]["debe"]
        for p in asistentes
    }
    return min(balances, key=balances.get)


@app.route("/")
def index():
    return render_template(
        "index.html",
        personas=PERSONAS,
        sugerido=None,
        asistentes=[]
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
            asistentes=[]
        )

    sugerido = sugerir_pagador(data, asistentes)

    return render_template(
        "index.html",
        personas=PERSONAS,
        sugerido=sugerido,
        asistentes=asistentes
    )


@app.route("/registrar", methods=["POST"])
def registrar():
    data = load()

    pagador = request.form["pagador"]
    asistentes = request.form.getlist("asistentes")

    if pagador not in asistentes:
        asistentes.append(pagador)

    total = sum(coste(p) for p in asistentes)

    for a in asistentes:
        if a != pagador:
            data[a]["debe"] += coste(a)

    data[pagador]["pagado"] += (total - coste(pagador))

    save(data)

    return redirect("/")
