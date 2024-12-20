import requests
import time
from database import get_db_connection  # Veritabanı bağlantısı

# ExchangeRate API anahtarı
EXCHANGERATE_API_KEY = "ae3a1b4145458a01849153bf"

def get_all_crypto_prices():
    """
    Binance API'den kripto para fiyatlarını çeker.
    """
    url = "https://api.binance.com/api/v3/ticker/price"
    response = requests.get(url)
    if response.status_code != 200: 
        print("Binance API isteği başarısız oldu:", response.status_code, response.text)
        return {}
    
    data = response.json()
    return {item["symbol"]: float(item["price"]) for item in data}

def get_all_currency_rates():
    """
    ExchangeRate API'den döviz fiyatlarını çeker.
    Döviz oranları 1 birimin kaç TL olduğunu gösterecek şekilde ayarlanır.
    """
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/TRY"
    response = requests.get(url)
    if response.status_code != 200:
        print("ExchangeRate API isteği başarısız oldu:", response.status_code, response.text)
        return {}
    
    data = response.json()
    rates = data.get("conversion_rates", {})
    
    # 1 birimin kaç TL olduğunu hesaplar (TL'ye bölerek tersine çevirir)
    try:
        tl_rate = rates["TRY"]
    except KeyError:
        print("TRY oranı bulunamadı.")
        return {}

    return {currency: round(1 / rate, 5) for currency, rate in rates.items() if rate > 0}

def update_crypto_prices():
    """
    Veritabanındaki kripto para fiyatlarını Binance API'den güncelleyerek günceller.
    """
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
            try:
                current_price = round(float(all_prices[coin_symbol]), 5)  # Fiyatı 5 basamakla sınırla
            except (ValueError, TypeError):
                print(f"{coin_symbol} için fiyat yuvarlanamadı.")
                continue

            current_time = time.strftime('%Y-%m-%d %H:%M:%S')

            crypto_collection.update_one(
                {'_id': coin['_id']},
                {'$set': {'guncel_fiyat': current_price, 'guncellenme_zamani': current_time}}
            )
            print(f"{coin_symbol} fiyatı güncellendi: {current_price}")

def update_currency_prices():
    """
    Veritabanındaki döviz fiyatlarını ExchangeRate API'den güncelleyerek günceller.
    Döviz fiyatlarını 1 birimin kaç TL olduğunu gösterecek şekilde günceller.
    """
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
            try:
                current_price_in_try = all_rates[currency_name]
            except (ValueError, TypeError):
                print(f"{currency_name} için fiyat hesaplanamadı.")
                continue

            current_time = time.strftime('%Y-%m-%d %H:%M:%S')

            currency_collection.update_one(
                {'_id': currency['_id']},
                {'$set': {'guncel_fiyat': current_price_in_try, 'guncellenme_zamani': current_time}}
            )
            print(f"{currency_name} fiyatı (1 {currency_name} kaç TL): {current_price_in_try}")

    """
    Kripto ve döviz fiyatlarının son 24 saatlik yüzdelik değişimini hesaplar.
    """
    db = get_db_connection()
    crypto_collection = db['Kripto Para']
    crypto_history = db['Kripto_Gecmis']
    currency_collection = db['Döviz']
    currency_history = db['Döviz_Gecmis']

    # Sonuçları tutacak dictionary
    percentage_changes = {
        'kripto': {},
        'doviz': {}
    }

    # Kripto paralar için yüzdelik değişim hesaplama
    for coin in crypto_collection.find():
        # Geçmişteki fiyatları al
        past_prices = list(crypto_history.find(
            {'kripto_id': coin['_id'], 'tarih': {'$gte': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() - 86400))}}
        ).sort('tarih', 1))

        if not past_prices:
            continue

        initial_price = past_prices[0]['fiyat']
        current_price = coin['guncel_fiyat']

        # Yüzdelik değişim hesapla
        try:
            percentage_change = round(((current_price - initial_price) / initial_price) * 100, 2)
        except ZeroDivisionError:
            percentage_change = 0.0

        # Sonuçları kaydet
        percentage_changes['kripto'][coin['kripto_adi']] = percentage_change

    # Dövizler için yüzdelik değişim hesaplama
    for currency in currency_collection.find():
        # Geçmişteki fiyatları al
        past_prices = list(currency_history.find(
            {'döviz_id': currency['_id'], 'tarih': {'$gte': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() - 86400))}}
        ).sort('tarih', 1))

        if not past_prices:
            continue

        initial_price = past_prices[0]['fiyat']
        current_price = currency['guncel_fiyat']

        # Yüzdelik değişim hesapla
        try:
            percentage_change = round(((current_price - initial_price) / initial_price) * 100, 2)
        except ZeroDivisionError:
            percentage_change = 0.0

        # Sonuçları kaydet
        percentage_changes['doviz'][currency['döviz_adi']] = percentage_change

    print(percentage_changes)
    return percentage_changes


def save_prices_to_history():
    """
    Kripto ve döviz fiyatlarını geçmiş koleksiyonlara kaydeder.
    """
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
    """
    Kripto ve döviz fiyatlarını düzenli olarak günceller ve geçmiş kaydeder.
    """
    update_count = 0
    while True:
        update_crypto_prices()
        update_currency_prices()
        update_count += 1

        if update_count % 2 == 0:
            save_prices_to_history()

        time.sleep(30)  # 30 saniyede bir fiyat güncellemesi

# Kullanım
if __name__ == "__main__":
    start_price_updater()
