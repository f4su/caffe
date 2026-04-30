import psycopg2
import os
import json

DATABASE_URL = os.environ.get("DATABASE_URL")


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

    cur.execute("SELECT * FROM app_data LIMIT 1;")
    if cur.fetchone() is None:
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

    return row[0] if row else {}


def save_data(data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("UPDATE app_data SET data = %s WHERE id = 1;", [json.dumps(data)])

    conn.commit()
    cur.close()
    conn.close()
