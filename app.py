from flask import Flask, render_template, request, redirect, url_for, session
import hashlib
import sqlite3

app = Flask(__name__)
app.secret_key = 'cryptoapex_x'

# Veritabanı bağlantısı
def get_db_connection():
    conn = sqlite3.connect('cryptoapex.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password.encode('utf-8'))
    return sha256_hash.hexdigest()

# Veritabanını oluşturma
def create_database():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.close()

create_database()

# Kayıt Ol Sayfası
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        hashed_password = hash_password(password)
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed_password)
            )
            conn.commit()
            message = 'Kayıt başarılı! Artık giriş yapabilirsiniz.'
            return render_template('register.html', message=message)
        except sqlite3.IntegrityError:
            message = 'Bu kullanıcı adı veya e-posta zaten kayıtlı.'
        finally:
            conn.close()

    return render_template('register.html', message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        username_or_email = request.form['username-email']
        password = request.form['password']
        hs_password = hash_password(password)
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username_or_email, username_or_email)).fetchone()
        conn.close()

        if user:
            if hs_password == user["password"]:
                session['user_id'] = user['id']
                session['username'] = user['username']
                message = 'Giriş başarılı!'
                return render_template('index.html', message=message)
            else:
                message = 'Kullanıcı adı veya şifre hatalı.'
        else:
            message = 'Kullanıcı adı veya şifre hatalı.'

    return render_template('login.html', message=message)


# Anasayfa
@app.route('/', methods=['GET'])
def index():
    #if 'user_id' not in session:
        #return redirect(url_for('login'))
    return render_template('index.html')

# Çıkış Yapma
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    message = 'Çıkış yapıldı.'
    return render_template('login.html', message=message)


# dasdasdasdas
if __name__ == '__main__':
    app.run(debug=True)
