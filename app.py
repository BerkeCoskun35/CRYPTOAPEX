from flask import Flask, jsonify, render_template, request, session
import hashlib
from database import get_db_connection
from api import start_price_updater
import threading
from bson.objectid import ObjectId
import pandas as pd
import plotly.graph_objects as go
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time

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

    crypto_prices = list(crypto_collection.find().sort('kripto_adi', 1))

    updated_crypto_prices = [
        {
            '_id': str(item['_id']),
            'kripto_adi': item['kripto_adi'],
            'kripto_icon': item['kripto_icon'],
            'guncel_fiyat': item['guncel_fiyat']
        }
        for item in crypto_prices
    ]
    return updated_crypto_prices

def get_updated_currency_prices():
    db = get_db_connection()
    currency_collection = db['Döviz']

    currency_prices = list(currency_collection.find().sort('döviz_adi', 1))

    updated_currency_prices = [
        {
            '_id': str(item['_id']),
            'döviz_adi': item['döviz_adi'],
            'döviz_icon': item['döviz_icon'],
            'guncel_fiyat': item['guncel_fiyat']
        }
        for item in currency_prices
    ]
    return updated_currency_prices


# Fetch historical data for a specific item
def get_historical_data(item_name, item_type):
    """
    Belirli bir öğenin tarihsel verilerini alır ve DataFrame olarak döndürür.
    """
    db = get_db_connection()
    collection = db["Kripto_Gecmis"] if item_type == "crypto" else db["Döviz_Gecmis"]

    # İsme göre sorgu
    query = {"crypto_name": item_name} if item_type == "crypto" else {"currency_name": item_name}
    print("Sorgu:", query)  # Debugging için log
    history = list(collection.find(query))

    if not history:
        print("Veritabanında tarihsel veri bulunamadı.")
        return pd.DataFrame()

    # DataFrame'e dönüştür
    df = pd.DataFrame(history)
    print("Çekilen veriler:", df.head())  # Debugging için log

    # Eksik sütun kontrolü
    required_columns = {"open_time", "close_time", "open", "high", "low", "close"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        print("Eksik sütunlar:", missing_columns)
        return pd.DataFrame()

    # Zaman verilerini pandas datetime formatına dönüştür
    df["open_time"] = pd.to_datetime(df["open_time"], errors="coerce")
    df["close_time"] = pd.to_datetime(df["close_time"], errors="coerce")

    return df



# Generate a historical chart
def generate_chart(df, item_name):
    """
    Tarihsel veri kullanarak Binance tarzı mum grafiği oluşturur.
    Fare ile basılı tutarak sürükleme (pan) ve zoom özellikleri desteklenir.
    """
    # Eksik sütunları kontrol et
    required_columns = {"open_time", "open", "high", "low", "close"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Eksik sütunlar: {missing_columns}")

    # Mum grafiği oluştur
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["open_time"],       # Zaman ekseni
                open=df["open"],         # Açılış fiyatları
                high=df["high"],         # En yüksek fiyatlar
                low=df["low"],           # En düşük fiyatlar
                close=df["close"],       # Kapanış fiyatları
                increasing=dict(line=dict(color="#0fdb8c")),  # Yükselen mumlar (yeşil)
                decreasing=dict(line=dict(color="#f23030")),  # Düşen mumlar (kırmızı)
                name=item_name           # Grafik başlığı
            )
        ]
    )

    # Grafik düzenlemeleri
    fig.update_layout(
        title=dict(
            text=f"{item_name} Mum Grafiği",
            x=0.5,  # Ortalamak için
            font=dict(
                size=24,
                color="white"
            )
        ),
        xaxis_title="Zaman",
        yaxis_title="Fiyat (USD)",
        template="plotly_dark",  # Modern ve koyu bir tema
        height=600,              # Grafik yüksekliği
        margin=dict(l=50, r=50, t=50, b=50),  # Grafik kenar boşlukları
        font=dict(
            family="Roboto, Arial, sans-serif",
            size=14,
            color="white"
        ),
        plot_bgcolor="#1a1a1a",   # Grafik arka planı
        paper_bgcolor="#1a1a1a",  # Dış arka plan
        hovermode="x unified",    # Hover etkisi için tüm eksenleri birleştir
        dragmode="pan",           # Fare ile sürükleme (pan) modu
    )

    # Zaman ekseni ayarları
    fig.update_xaxes(
        rangeslider=dict(visible=True, bgcolor="#333"),  # Zaman kaydırıcısı
        tickformat="%Y-%m-%d %H:%M",                    # Tarih formatı
        showgrid=True,                                  # Grid çizgileri
        gridcolor="#444"                                # Grid çizgileri rengi
    )

    # Fiyat ekseni için dinamik ölçekleme
    fig.update_yaxes(
        autorange=True,              # Y ekseni dinamik olarak ölçeklensin
        fixedrange=False,            # Y ekseni serbest zoom yapabilsin
        tickformat=".2f",            # 2 ondalık gösterim
        showgrid=True,               # Grid çizgileri
        gridcolor="#444",            # Grid çizgileri rengi
    )

    # Fare tekerleği ile zoom ve pan gibi etkileşimleri etkinleştir
    config = {
        "scrollZoom": True,  # Fare tekerleği ile zoom yapmayı etkinleştirir
        "displayModeBar": True,  # Mod çubuğunu her zaman görünür yapar
        "displaylogo": False,  # Plotly logosunu kaldırır
    }

    # HTML olarak döndür
    return fig.to_html(full_html=False, config=config)




@app.route("/details/<item_type>/<item_name>")
def show_details(item_type, item_name):
    db = get_db_connection()

    # Veritabanı sorgusu
    if item_type == "crypto":
        item = db["Kripto_Gecmis"].find_one({"crypto_name": item_name})
        if not item:
            return render_template("details.html", chart_html=None, item_name=item_name, error="No data found for the selected cryptocurrency.")
    else:
        item = db["Döviz_Gecmis"].find_one({"currency_name": item_name})
        if not item:
            return render_template("details.html", chart_html=None, item_name=item_name, error="No data found for the selected currency.")

    # Tarihsel verileri al
    df = get_historical_data(item_name, item_type)  # item_id yerine item_name gönderiliyor
    if df.empty:
        return render_template("details.html", chart_html=None, item_name=item_name, error="No historical data available.")

    # Grafik oluşturma
    try:
        chart_html = generate_chart(df, item_name)
    except ValueError as e:
        print("Grafik oluşturma hatası:", str(e))
        return render_template("details.html", chart_html=None, item_name=item_name, error=str(e))

    # Başarılı sonuç döndür
    return render_template("details.html", chart_html=chart_html, item_name=item_name)



def format_price(price):
    try:
        # Convert to float if it is in scientific notation
        float_price = float(price)
        # Format to 5 decimal places and remove trailing zeros
        return "{:.5f}".format(float_price).rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        # Return the price as-is if formatting fails
        return str(price)

# @app.route('/')
# def index():
#     user_id = session.get('user_id')
#     db = get_db_connection()
#     updated_crypto_prices = get_updated_crypto_prices()
#     updated_currency_prices = get_updated_currency_prices()
#     user_favorites = set()  # Use a set for faster lookups
#     if user_id:
#         favorites = db['favorites'].find({'user_id': ObjectId(user_id)})
#         user_favorites = {fav['name'] for fav in favorites}  # Collect only names
#     return render_template('index.html', updated_crypto_prices=updated_crypto_prices, updated_currency_prices=updated_currency_prices, user_favorites=user_favorites)

@app.route('/')
def index():
    user_id = session.get('user_id')
    db = get_db_connection()
    updated_crypto_prices = get_updated_crypto_prices()
    updated_currency_prices = get_updated_currency_prices()
    
    user_favorites = set()  # Kullanıcının favorilerini saklamak için set
    if user_id:
        favorites = db['favorites'].find({'user_id': ObjectId(user_id)})
        user_favorites = {fav['name'] for fav in favorites}  # Favori isimlerini set'e ekliyoruz

    # Favorilere öncelik vererek sıralama yapıyoruz
    sorted_crypto_prices = sorted(updated_crypto_prices, key=lambda x: (x['kripto_adi'] not in user_favorites, x['kripto_adi']))
    sorted_currency_prices = sorted(updated_currency_prices, key=lambda x: (x['döviz_adi'] not in user_favorites, x['döviz_adi']))

    return render_template('index.html', updated_crypto_prices=sorted_crypto_prices, updated_currency_prices=sorted_currency_prices, user_favorites=user_favorites)


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
