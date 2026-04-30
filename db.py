import psycopg2
import os
import json

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL no está configurada en Render")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


# =========================
# 📦 INICIALIZACIÓN BD
# =========================
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # estado global
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            id SERIAL PRIMARY KEY,
            data JSONB
        );
    """)

    # historial de eventos (APPEND ONLY)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            pagador TEXT NOT NULL,
            asistentes TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # asegurar fila única
    cur.execute("SELECT COUNT(*) FROM app_data;")
    count = cur.fetchone()[0]

    if count == 0:
        cur.execute(
            "INSERT INTO app_data (data) VALUES (%s);",
            [json.dumps({})]
        )

    conn.commit()
    cur.close()
    conn.close()


# =========================
# 📊 ESTADO GENERAL
# =========================
def get_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT data FROM app_data LIMIT 1;")
    row = cur.fetchone()

    cur.close()
    conn.close()

    return row[0] if row and row[0] else {}


def save_data(data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE app_data SET data = %s WHERE id = 1;",
        [json.dumps(data)]
    )

    conn.commit()
    cur.close()
    conn.close()


# =========================
# 🧾 EVENTOS (HISTORIAL)
# =========================
def add_transaction(pagador, asistentes, cantidad):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO transactions (pagador, asistentes, cantidad)
        VALUES (%s, %s, %s);
    """, [pagador, ",".join(asistentes), cantidad])

    conn.commit()
    cur.close()
    conn.close()


def get_transactions(limit=4):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT pagador, asistentes, cantidad
        FROM transactions
        ORDER BY id DESC
        LIMIT %s;
    """, [limit])

    rows = cur.fetchall()

    cur.close()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "pagador": r[0],
            "asistentes": r[1].split(",") if r[1] else [],
            "cantidad": r[2]
        })

    return result[::-1]


# =========================
# ❌ BORRAR ÚLTIMO (UNDO REAL)
# =========================
def delete_last_transaction():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, pagador, asistentes, cantidad
        FROM transactions
        ORDER BY id DESC
        LIMIT 1;
    """)

    row = cur.fetchone()

    if not row:
        conn.close()
        return None

    tx_id, pagador, asistentes, cantidad = row

    # ❌ aquí ya NO borramos ni marcamos nada
    # solo devolvemos el evento para revertir lógica
    cur.execute("DELETE FROM transactions WHERE id = %s;", [tx_id])

    conn.commit()
    cur.close()
    conn.close()

    return {
        "pagador": pagador,
        "asistentes": asistentes.split(",") if asistentes else [],
        "cantidad": cantidad
    }


# =========================
# 🔁 REVERTIR ESTADO
# =========================
def revert_transaction(data, tx):
    if not tx:
        return data

    pagador = tx["pagador"]
    asistentes = tx["asistentes"]
    cantidad = tx["cantidad"]

    for a in asistentes:
        if a in data:
            data[a]["consumido"] = max(0, data[a].get("consumido", 0) - 1)

    if pagador in data:
        data[pagador]["pagado"] = max(0, data[pagador].get("pagado", 0) - cantidad)

    return data
