import sqlite3

def get_db_connection():
    conn = sqlite3.connect('cryptoapex.db')
    conn.row_factory = sqlite3.Row   #veritabanındaki verilerin satırlarını döndürür.verilere erişmeyi kolaylaştırır.
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
    conn.commit()  # Bağlantı üzerindeki değişiklikleri kaydedin

def select_in(conn):
    output = conn.execute('''
        SELECT * FROM users
    ''')
    rows = output.fetchall()  # Verileri çekin
    for row in rows:
        print(dict(row))  # Satırları sözlük olarak yazdırın.(böylece verileri sütun isimleriyle görürüz)

conn = get_db_connection()
create_database(conn)
select_in(conn)
conn.close()  # Bağlantıyı işlemler tamamlandıktan sonra kapatın