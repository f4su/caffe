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


@app.route("/")
def index():
    data = load()
    return render_template("index.html", personas=PERSONAS, data=data)


@app.route("/registrar", methods=["POST"])
def registrar():
    data = load()

    pagador = request.form["pagador"]
    asistentes = request.form["asistentes"]

    asistentes = [a.strip() for a in asistentes.split(",") if a.strip()]

    if pagador not in asistentes:
        asistentes.append(pagador)

    # 🔥 calcular total del grupo
    total_grupo = 0
    for a in asistentes:
        total_grupo += coste(a)

    # 🔥 cada uno paga su consumo
    for a in asistentes:
        if a == pagador:
            # el pagador NO se cuenta a sí mismo
            continue

        data[a]["debe"] += coste(a)

    # 🔥 el pagador paga todo menos su propia consumición
    data[pagador]["pagado"] += (total_grupo - coste(pagador))

    save(data)

    return redirect("/")
