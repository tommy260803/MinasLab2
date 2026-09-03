import psycopg2

password = "postgres"
conn = psycopg2.connect(dbname="predictive_maintenance_db", user="postgres", password=password, host="localhost")
cur = conn.cursor()

# Regenerate seed_data.sql
import subprocess, sys
subprocess.run([sys.executable, "database/generate_sql.py"], check=True)

with open('database/schema.sql', 'r', encoding='utf-8') as f:
    cur.execute(f.read())
with open('database/seed_data.sql', 'r', encoding='utf-8') as f:
    cur.execute(f.read())

conn.commit()
cur.close()
conn.close()
print("Success")
