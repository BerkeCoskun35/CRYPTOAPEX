from flask import Flask, jsonify, render_template, request, session
import hashlib
from database import get_db_connection
from api import start_price_updater
import threading

app = Flask(__name__)
app.secret_key = 'cryptoapex_x'

def hash_password(password):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password.encode('utf-8'))
    return sha256_hash.hexdigest()

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = hash_password(password)

        db = get_db_connection()
        users = db['users']
        try:
            users.insert_one({
                'username': username,
                'email': email,
                'password': hashed_password
            })
            message = 'Kayıt başarılı! Artık giriş yapabilirsiniz.'
        except Exception as e:
            message = 'Bu kullanıcı adı veya e-postası zaten kayıtlı.'

    return render_template('register.html', message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        username_or_email = request.form.get('username-email')
        password = request.form.get('password')
        hs_password = hash_password(password)

        # MongoDB bağlantısı
        db = get_db_connection()
        users = db['users']
        
        # Kullanıcıyı sorgula
        user = users.find_one({'$or': [{'username': username_or_email}, {'email': username_or_email}]})
        
        # Kullanıcı doğrulama
        if user:
            if user.get('password') == hs_password:
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                message = 'Giriş başarılı!'
            else:
                message = 'Şifre hatalı.'
        else:
            message = 'Kullanıcı adı veya e-posta bulunamadı.'

        if message == 'Giriş başarılı!':
            updated_crypto_prices = get_updated_crypto_prices()
            updated_currency_prices = get_updated_currency_prices()
            return render_template('index.html', message=message, 
                                   updated_crypto_prices=updated_crypto_prices,
                                   updated_currency_prices=updated_currency_prices)

    return render_template('login.html', message=message)


def get_updated_crypto_prices():
    db = get_db_connection()
    crypto_collection = db['Kripto Para']

    # Kripto verilerini alfabetik sıralama ile al
    crypto_prices = list(crypto_collection.find().sort('kripto_adi', 1))  # 1 = Artan sıralama (A-Z)

    # Güncel fiyatları ve ikonları düzenle
    updated_crypto_prices = [
        {
            'kripto_adi': item['kripto_adi'],
            'kripto_icon': item['kripto_icon'],
            'guncel_fiyat': item['guncel_fiyat']
        } for item in crypto_prices
    ]

    return updated_crypto_prices

def get_updated_currency_prices():
    db = get_db_connection()
    currency_collection = db['Döviz']

    # Döviz verilerini alfabetik sıralama ile al
    currency_prices = list(currency_collection.find().sort('döviz_adi', 1))  # 1 = Artan sıralama (A-Z)

    # Güncel fiyatları ve ikonları düzenle
    updated_currency_prices = [
        {
            'döviz_adi': item['döviz_adi'],
            'döviz_icon': item['döviz_icon'],
            'guncel_fiyat': item['guncel_fiyat']
        } for item in currency_prices
    ]

    return updated_currency_prices


@app.route('/')
def index():
    updated_crypto_prices = get_updated_crypto_prices()
    updated_currency_prices = get_updated_currency_prices()
    return render_template('index.html', updated_crypto_prices=updated_crypto_prices, updated_currency_prices=updated_currency_prices)




@app.route('/api/prices', methods=['GET'])
def get_prices():
    updated_prices = get_updated_crypto_prices() + get_updated_currency_prices()  # Her iki tür fiyatları birleştiriyoruz
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
