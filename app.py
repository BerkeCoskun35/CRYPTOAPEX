from flask import Flask, jsonify, render_template, request, session
import hashlib
from database import get_db_connection, create_database
import sqlite3
from api import start_price_updater
import threading

app = Flask(__name__)
app.secret_key = 'cryptoapex_x'

def hash_password(password):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password.encode('utf-8'))
    return sha256_hash.hexdigest()


with get_db_connection() as conn:
    create_database(conn)

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
        except sqlite3.IntegrityError:
            message = 'Bu kullanıcı adı veya e-postası zaten kayıtlı.'
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
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', 
                            (username_or_email, username_or_email)).fetchone()
        conn.close()

        if user and hs_password == user["password"]:
            session['user_id'] = user['id']
            session['username'] = user['username']
            message = 'Giriş başarili!'

            updated_prices = get_updated_prices()
            return render_template('index.html', message=message, updated_prices=updated_prices)
        else:
            message = 'Kullanıcı adı veya şifresi hatalı.'

    return render_template('login.html', message=message)


def get_updated_prices():
    conn = get_db_connection()
    cursor = conn.cursor()

  
    cursor.execute("SELECT kripto_adi, guncel_fiyat FROM 'Kripto Para' WHERE kripto_adi IN ('BTC', 'ETH', 'SOL')")
    prices = cursor.fetchall()
    conn.close()
    
    
    updated_prices = {row['kripto_adi']: f"{row['guncel_fiyat']}" for row in prices}
    return updated_prices

@app.route('/')
def index():
    updated_prices = get_updated_prices()
    return render_template('index.html', updated_prices=updated_prices)

@app.route('/api/prices', methods=['GET'])
def get_prices():
    updated_prices = get_updated_prices()
    return jsonify(updated_prices)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    message = 'Çıkış yapıldı.'
    return render_template('login.html', message=message)


price_updater_thread = threading.Thread(target=start_price_updater, daemon=True)
price_updater_thread.start()

if __name__ == '__main__':
    app.run(debug=False)
