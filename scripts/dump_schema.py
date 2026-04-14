import mysql.connector

def dump():
    c = mysql.connector.connect(host='127.0.0.1', user='root', password='Mohak@12', database='student_helper')
    cur = c.cursor()
    
    cur.execute("SHOW TABLES")
    tables = [t[0] for t in cur.fetchall()]
    
    with open('schema.txt', 'w') as f:
        for t in tables:
            f.write(f"\nTABLE: {t}\n")
            cur.execute(f"DESCRIBE {t}")
            for row in cur.fetchall():
                f.write(f"  {row[0]} ({row[1]})\n")

dump()
