import psycopg2
import os
import json

# 🔥 Variable de entorno
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

    # tabla estado (JSON global)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            id SERIAL PRIMARY KEY,
            data JSONB
        );
    """)

    # tabla de transacciones (NUEVA)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            pagador TEXT NOT NULL,
            asistentes TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # asegurar fila única en app_data
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
# 📊 ESTADO GENERAL (JSON)
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
# 🧾 TRANSACCIONES
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
