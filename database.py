import sqlite3

def get_db_connection():
    conn = sqlite3.connect('cryptoapex.db') 
    conn.row_factory = sqlite3.Row 
    return conn

def create_database(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit() 

def select_in(conn):
    output = conn.execute('''
        SELECT * FROM users
    ''')
    rows = output.fetchall() 
    for row in rows:
        print(dict(row))  

conn = get_db_connection()
create_database(conn)
select_in(conn)
conn.close()  