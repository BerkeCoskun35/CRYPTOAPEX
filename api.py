import requests
import time
from database import get_db_connection

EXCHANGERATE_API_KEY = "6c1ce89d793965170ed70274"

def get_all_crypto_prices():
    url = "https://api.binance.com/api/v3/ticker/price"
    response = requests.get(url)
    if response.status_code != 200:
        print("Binance API isteği başarısız oldu:", response.status_code, response.text)
        return {}
    
    data = response.json()
    return {item["symbol"]: float(item["price"]) for item in data}

def get_all_currency_rates():
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/USD"
    response = requests.get(url)
    if response.status_code != 200:
        print("ExchangeRate API isteği başarısız oldu:", response.status_code, response.text)
        return {}
    
    data = response.json()
    if "conversion_rates" not in data:
        print("ExchangeRate API yanıtı beklenen formatta değil:", data)
        return {}
    
    conversion_rates = data["conversion_rates"]

    usd_to_try_rate = conversion_rates.get("TRY")
    if not usd_to_try_rate:
        print("TRY kur bilgisi bulunamadı.")
        return {}

    try_rates = {currency: usd_to_try_rate / rate for currency, rate in conversion_rates.items() if currency != "USD"}
    return try_rates

def update_crypto_prices():
    all_prices = get_all_crypto_prices()
    if not all_prices:
        print("Kripto fiyatları alınamadı.")
        return
    
    db = get_db_connection()
    crypto_collection = db['Kripto Para']

    coins = list(crypto_collection.find())
    for coin in coins:
        coin_symbol = coin["kripto_adi"] + "USDT"
        if coin_symbol in all_prices:
            current_price = all_prices[coin_symbol]
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')

            crypto_collection.update_one(
                {'_id': coin['_id']},
                {'$set': {'guncel_fiyat': current_price, 'guncellenme_zamani': current_time}}
            )
            print(f"{coin_symbol} fiyatı güncellendi: {current_price}")

def update_currency_prices():
    all_rates = get_all_currency_rates()
    if not all_rates:
        print("Döviz kurları alınamadı.")
        return
    
    db = get_db_connection()
    currency_collection = db['Döviz']

    currencies = list(currency_collection.find())
    for currency in currencies:
        currency_name = currency["döviz_adi"]
        if currency_name in all_rates:
            current_price_in_tl = all_rates[currency_name]
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')

            currency_collection.update_one(
                {'_id': currency['_id']},
                {'$set': {'guncel_fiyat': current_price_in_tl, 'guncellenme_zamani': current_time}}
            )
            print(f"{currency_name} fiyatı (1 birim kaç TL): {current_price_in_tl}")

def save_prices_to_history():
    db = get_db_connection()
    crypto_collection = db['Kripto Para']
    crypto_history = db['Kripto_Gecmis']

    for coin in crypto_collection.find():
        crypto_history.insert_one({
            'kripto_id': coin['_id'],
            'fiyat': coin['guncel_fiyat'],
            'tarih': time.strftime('%Y-%m-%d %H:%M:%S')
        })

    currency_collection = db['Döviz']
    currency_history = db['Döviz_Gecmis']

    for currency in currency_collection.find():
        currency_history.insert_one({
            'döviz_id': currency['_id'],
            'fiyat': currency['guncel_fiyat'],
            'tarih': time.strftime('%Y-%m-%d %H:%M:%S')
        })

    print("Fiyatlar geçmiş tablolara kaydedildi.")

def start_price_updater():
    update_count = 0
    while True:
        update_crypto_prices()
        update_currency_prices()
        update_count += 1

        if update_count % 2 == 0:
            save_prices_to_history()

        time.sleep(30)
