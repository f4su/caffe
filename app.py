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


def quien_paga(data):
    balances = {p: data[p]["pagado"] - data[p]["debe"] for p in PERSONAS}
    return min(balances, key=balances.get), balances


@app.route("/")
def index():
    data = load()
    pagador, balances = quien_paga(data)

    return render_template(
        "index.html",
        personas=PERSONAS,
        pagador=pagador,
        data=data,
        balances=balances
    )


@app.route("/registrar", methods=["POST"])
def registrar():
    data = load()

    pagador = request.form["pagador"]
    beneficiarios = request.form["beneficiarios"]

    beneficiarios = [b.strip() for b in beneficiarios.split(",") if b.strip()]

    total = 0

    for b in beneficiarios:
        if b in data:
            data[b]["debe"] += coste(b)
            total += coste(b)

    if pagador in data:
        data[pagador]["pagado"] += total

    save(data)

    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
