import bcrypt
import psycopg2
pw = bcrypt.hashpw(b'password123', bcrypt.gensalt(12)).decode('utf-8')
conn = psycopg2.connect(dbname="predictive_maintenance_db", user="postgres", password="postgres", host="localhost")
cur = conn.cursor()
cur.execute("UPDATE users SET password_hash = %s", (pw,))
conn.commit()
print("Passwords updated successfully to 'password123'. Hash used:", pw)

