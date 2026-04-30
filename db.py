import psycopg2
import os
import json

# 🔥 Leer variable de entorno de forma segura
DATABASE_URL = os.getenv("DATABASE_URL")

# 🚨 Fail rápido si no está configurada (MUY IMPORTANTE)
if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL no está configurada en Render")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            id SERIAL PRIMARY KEY,
            data JSONB
        );
    """)

    # ⚠️ asegurar que exista una fila única
    cur.execute("SELECT COUNT(*) FROM app_data;")
    count = cur.fetchone()[0]

    if count == 0:
        cur.execute("INSERT INTO app_data (data) VALUES (%s);", [json.dumps({})])

    conn.commit()
    cur.close()
    conn.close()


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
