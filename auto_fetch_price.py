import streamlit as st
import time
import requests
import logging
from pymongo import MongoClient

EXCHANGERATE_API_KEY = "ae3a1b4145458a01849153bf"

# Configure logging
logging.basicConfig(
    filename='cryptoapex.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# MongoDB bağlantısını kuran fonksiyon
def get_db_connection():
    try:
        client = MongoClient('mongodb+srv://berkecoskun:Berke1035208@cluster0.ydrox.mongodb.net/')  # MongoDB'nin çalıştığı adres
        db = client['CryptoApex']  # Veritabanı adı
        logging.info("MongoDB bağlantısı başarıyla kuruldu.")
        return db
    except Exception as e:
        logging.error(f"MongoDB bağlantısı kurulamadı: {e}")
        return None

# Veritabanından kullanıcıları okuma
def select_in(db):
    try:
        users = db['users']
        for user in users.find():  # Tüm kullanıcıları al
            logging.info(f"Kullanıcı bulundu: {user}")
    except Exception as e:
        logging.error(f"Veritabanından kullanıcı okuma başarısız: {e}")

# API Verisi alma
def get_all_crypto_prices():
    url = "https://api.binance.com/api/v3/ticker/price"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        logging.info("Kripto para fiyatları başarıyla alındı.")
        return {item["symbol"]: float(item["price"]) for item in data}
    except Exception as e:
        logging.error(f"Binance API isteği başarısız oldu: {e}")
        return {}

def get_all_currency_rates():
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/TRY"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        rates = data.get("conversion_rates", {})
        logging.info("Döviz fiyatları başarıyla alındı.")
        return {currency: round(1 / rate, 5) for currency, rate in rates.items() if rate > 0}
    except Exception as e:
        logging.error(f"ExchangeRate API isteği başarısız oldu: {e}")
        return {}

# Fiyat güncelleme
def update_crypto_prices():
    """
    Updates cryptocurrency prices in the database. If a cryptocurrency is missing, it is inserted.
    """
    db = get_db_connection()
    if db is None:
        logging.error("Database connection failed. Skipping update.")
        return

    all_prices = get_all_crypto_prices()
    if not all_prices:
        logging.error("No cryptocurrency prices were retrieved. Skipping update.")
        return
    
    crypto_collection = db['Kripto_Gecmis']
    try:
        for symbol, price in all_prices.items():
            crypto_name = symbol.replace("USDT", "")  # Extract the cryptocurrency name
            
            # Check if the document exists
            existing_coin = crypto_collection.find_one({'kripto_adi': crypto_name})
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')

            if existing_coin and False:
                # Update the existing document
                crypto_collection.update_one(
                    {'_id': existing_coin['_id']},
                    {'$set': {'guncel_fiyat': round(price, 5), 'guncellenme_zamani': current_time}}
                )
                #logging.info(f"Updated {crypto_name} with price {round(price, 5)}")
            else:
                # Insert a new document
                crypto_collection.insert_one({
                    'kripto_adi': crypto_name,
                    'fiyat': round(price, 5),
                    'tarih': current_time
                })
                #logging.info(f"Inserted {crypto_name} with price {round(price, 5)}")
    except Exception as e:
        logging.error(f"Error while updating/inserting cryptocurrency prices: {e}")


def update_currency_prices():
    """
    Updates currency prices in the database. If a currency is missing, it is inserted.
    """
    db = get_db_connection()
    if db is None:
        logging.error("Database connection failed. Skipping update.")
        return

    all_rates = get_all_currency_rates()
    if not all_rates:
        logging.error("No currency rates were retrieved. Skipping update.")
        return

    currency_collection = db['Döviz_Gecmis']
    try:
        for currency, rate in all_rates.items():
            # Check if the document exists
            existing_currency = currency_collection.find_one({'döviz_adi': currency})
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')

            if existing_currency and False:
                # Update the existing document
                currency_collection.update_one(
                    {'_id': existing_currency['_id']},
                    {'$set': {'guncel_fiyat': rate, 'guncellenme_zamani': current_time}}
                )
                #logging.info(f"Updated {currency} with rate {rate}")
            else:
                # Insert a new document
                currency_collection.insert_one({
                    'döviz_adi': currency,
                    'fiyat': rate,
                    'tarih': current_time
                })
                #logging.info(f"Inserted {currency} with rate {rate}")
    except Exception as e:
        logging.error(f"Error while updating/inserting currency prices: {e}")


# Streamlit app layout
st.title("CryptoApex: Cryptocurrency and Currency Tracker")

tab1, tab2 = st.tabs(["Cryptocurrency Prices", "Currency Prices"])

# Cryptocurrency Prices
with tab1:
    st.header("Cryptocurrency Prices")
    if st.button("Update Crypto Prices Now", key="update_crypto"):
        update_crypto_prices()
        st.success("Cryptocurrency prices updated!")

# Currency Prices
with tab2:
    st.header("Currency Prices")
    if st.button("Update Currency Prices Now", key="update_currency"):
        update_currency_prices()
        st.success("Currency prices updated!")
