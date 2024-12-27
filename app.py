from flask import Flask, jsonify, render_template, request, session
import hashlib
from database import get_db_connection
from api import start_price_updater
import threading
from bson.objectid import ObjectId

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
            'guncel_fiyat': format_price(item['guncel_fiyat'])
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
            'guncel_fiyat': format_price(item['guncel_fiyat'])
        } for item in currency_prices
    ]

    return updated_currency_prices

def format_price(price):
    try:
        # Convert to float if it is in scientific notation
        float_price = float(price)
        # Format to 5 decimal places and remove trailing zeros
        return "{:.5f}".format(float_price).rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        # Return the price as-is if formatting fails
        return str(price)

@app.route('/')
def index():
    user_id = session.get('user_id')
    db = get_db_connection()
    updated_crypto_prices = get_updated_crypto_prices()
    updated_currency_prices = get_updated_currency_prices()
    user_favorites = set()  # Use a set for faster lookups
    if user_id:
        favorites = db['favorites'].find({'user_id': ObjectId(user_id)})
        user_favorites = {fav['name'] for fav in favorites}  # Collect only names
    return render_template('index.html', updated_crypto_prices=updated_crypto_prices, updated_currency_prices=updated_currency_prices, user_favorites=user_favorites)

@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Kullanıcı giriş yapmamış.'}), 401
    user_id = session['user_id']
    db = get_db_connection()
    favorites = db['favorites'].find({'user_id': ObjectId(user_id)})
    return jsonify({'success': True, 'favorites': [{'name': fav['name'], 'type': fav['type']} for fav in favorites]})

@app.route('/api/favorite', methods=['POST'])
def toggle_favorite():
    try:
        if 'user_id' not in session:
            print("Session error: user_id not found.")
            return jsonify({'success': False, 'message': 'Kullanıcı giriş yapmamış.'}), 401

        user_id = session['user_id']
        print("User ID from session:", user_id)

        data = request.json
        print("Received data:", data)

        item_type = data.get('type')
        item_name = data.get('name')

        if not item_type or not item_name:
            print("Validation error: Missing type or name.")
            return jsonify({'success': False, 'message': 'Eksik veri gönderildi.'}), 400

        db = get_db_connection()
        print("Database connection established.")
        favorites = db['favorites']

        try:
            user_id_object = ObjectId(user_id)
        except Exception as id_error:
            print("Error converting user_id to ObjectId:", id_error)
            return jsonify({'success': False, 'message': 'Geçersiz user_id'}), 400

        existing_favorite = favorites.find_one({'user_id': user_id_object, 'type': item_type, 'name': item_name})
        if existing_favorite:
            favorites.delete_one({'_id': existing_favorite['_id']})
            print("Favorite removed:", existing_favorite)
            return jsonify({'success': True, 'action': 'removed'})

        new_favorite = {'user_id': user_id_object, 'type': item_type, 'name': item_name}
        favorites.insert_one(new_favorite)
        print("Favorite added:", new_favorite)
        return jsonify({'success': True, 'action': 'added'})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'success': False, 'message': str(e)}), 500



@app.route('/api/prices', methods=['GET'])
def get_prices():
    updated_prices = get_updated_crypto_prices() + get_updated_currency_prices()  # Her iki tür fiyatları birleştiriyoruz
    return jsonify(updated_prices)

@app.route('/api/check-login', methods=['GET'])
def check_login():
    if 'user_id' in session:
        return jsonify({'isLoggedIn': True})
    return jsonify({'isLoggedIn': False})


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
