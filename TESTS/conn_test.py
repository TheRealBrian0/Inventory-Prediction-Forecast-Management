import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="syscodb"
    )
except Exception as e:
    raise ValueError(f"Connection failed: {e}")


cursor = conn.cursor()
print("connection done \n")
cursor.execute("SELECT * FROM products")

for row in cursor:
    print(row)

cursor.close()
conn.close()