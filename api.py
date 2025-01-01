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

def format_price(price):
    """
    Fiyatları düzenler:
    - Eğer fiyat çok küçükse virgülden sonra maksimum 6 basamak gösterir.
    - Gereksiz sıfırları ve noktaları kaldırır.
    """
    try:
        price = float(price)  # Fiyatı float'a çevir
        if price < 0.000001:  # Çok küçük sayılar için
            return "{:.6f}".format(price).rstrip('0').rstrip('.')
        return "{:.6f}".format(price).rstrip('0').rstrip('.')  # Maksimum 6 basamak ve gereksiz sıfırları kaldır
    except ValueError:
        return str(price)  # Eğer hata oluşursa olduğu gibi döndür



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
                # Fiyatı formatla
                current_price = format_price(all_prices[coin_symbol])
            except (ValueError, TypeError):
                print(f"{coin_symbol} için fiyat formatlanamadı.")
                continue

            current_time = time.strftime('%Y-%m-%d %H:%M:%S')

            # Veritabanını güncelle
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
    Veritabanında yer alan kripto paralarla filtrelenmiş fiyatları kaydeder.
    Fiyatlar, küçük değerlerde maksimum 6 ondalık basamak ile formatlanır.
    """
    all_prices = get_all_crypto_prices()
    if not all_prices:
        print("Kripto fiyatları alınamadı.")
        return
    
    db = get_db_connection()
    crypto_history = db['Kripto_Gecmis']
    crypto_collection = db['Kripto Para']

    # Veritabanında kayıtlı olan kripto paraların isimlerini al
    db_crypto_names = [coin["kripto_adi"] for coin in crypto_collection.find()]

    current_time = time.time()
    hour_start = time.strftime('%Y-%m-%d %H:00:00', time.gmtime(current_time))
    hour_end = time.strftime('%Y-%m-%d %H:59:59', time.gmtime(current_time))

    for symbol, price in all_prices.items():
        # Sadece USDT tabanlı ve veritabanında kayıtlı olan kripto paraları işleme alıyoruz
        if not symbol.endswith('USDT'):
            continue

        crypto_name = symbol.replace('USDT', '')

        if crypto_name not in db_crypto_names:
            continue  # Veritabanında olmayanları atla

        # Fiyatı formatla
        formatted_price = format_price(price)

        # Daha önce kaydedilmiş bir saatlik dilim varsa, o kaydı güncelle
        existing_record = crypto_history.find_one({
            "crypto_name": crypto_name,
            "open_time": hour_start
        })

        if existing_record:
            # Mevcut kaydı güncelle
            updated_data = {
                "high": max(float(existing_record["high"]), float(formatted_price)),
                "low": min(float(existing_record["low"]), float(formatted_price)),
                "close": formatted_price,
                "close_time": hour_end,
            }
            crypto_history.update_one(
                {"_id": existing_record["_id"]},
                {"$set": updated_data}
            )
            print(f"{crypto_name} için mevcut saatlik kayıt güncellendi: {updated_data}")
        else:
            # Yeni bir saatlik dilim kaydı oluştur
            new_data = {
                "crypto_name": crypto_name,
                "open_time": hour_start,
                "open": formatted_price,
                "high": formatted_price,
                "low": formatted_price,
                "close": formatted_price,
                "close_time": hour_end
            }
            crypto_history.insert_one(new_data)
            print(f"{crypto_name} için yeni saatlik kayıt oluşturuldu: {new_data}")




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

        time.sleep(20000)  # 30 saniyede bir fiyat güncellemesi

# Kullanım
if __name__ == "__main__":
    start_price_updater()
