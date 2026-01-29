import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    print("Attempting to create vector extension...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    print("Success! pgvector is available.")
    conn.commit()
    cur.close()
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")

