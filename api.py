import requests
import time
from database import get_db_connection

# ExchangeRate API anahtarınızı buraya ekleyin
EXCHANGERATE_API_KEY = "6c1ce89d793965170ed70274"

# Binance API'sinden tüm kripto paraların fiyatlarını çekme fonksiyonu
def get_all_crypto_prices():
    url = "https://api.binance.com/api/v3/ticker/price" #binance api'ine ait kripto paraları çekmek için url
    response = requests.get(url)  #url'ye bir get isteği atıyoruz ve cevabı response'ye kaydediyoruz
    if response.status_code != 200:  #api isteğinin başarısız olup olmadıgını kontrol ediyoruz. 200 başarılı bir istek demek
        print("Binance API isteği başarısız oldu:", response.status_code, response.text)
        return {}
    
    data = response.json() #api cevabını json formatında data'ya atıyoruz.
    return {item["symbol"]: float(item["price"]) for item in data}#her bir kripto paranın sembol ve fiyatını sözlük olark g. döndürüyoruz.

# ExchangeRate API'sinden USD ve TRY kurlarını çekme fonksiyonu
def get_all_currency_rates():
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/USD" #exc.rate api url tanımladık.temel para birim usd seçtik.
    response = requests.get(url)  #url'ye bir get isteği atıyoruz.
    if response.status_code != 200:
        print("ExchangeRate API isteği başarısız oldu:", response.status_code, response.text)
        return {}
    
    data = response.json()
    if "conversion_rates" not in data: #api'den gelen verilerin beklenen formatta olup olmadıgını kontrol ediyoruz.
        print("ExchangeRate API yanıtı beklenen formatta değil:", data)
        return {}
    
    conversion_rates = data["conversion_rates"]

    # USD'den TRY'ye dönüşüm oranını al
    usd_to_try_rate = conversion_rates.get("TRY")
    if not usd_to_try_rate:
        print("TRY kur bilgisi bulunamadı.")
        return {}

    # Her döviz birimini USD cinsinden al ve TL'ye çevir
    try_rates = {currency: usd_to_try_rate / rate for currency, rate in conversion_rates.items() if currency != "USD"}
    return try_rates

# Veritabanındaki tüm kripto paraların fiyatlarını güncelle
def update_crypto_prices():
    all_prices = get_all_crypto_prices() 
    if not all_prices:  #api başarısız olmuşsa veya geriye değer dönmemişse hata mesajı yazdır ve fonksiyondan çık.
        print("Kripto fiyatları alınamadı.")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()  # cursor nesnesi veritabanı üzerinde sorgular çalıştırmamızı sağlar

    # Tüm kripto paraları seç
    cursor.execute("SELECT id, kripto_adi FROM 'Kripto Para'")
    coins = cursor.fetchall()  #sorgunun tüm sonuçlarını coins'e ata

    # Tüm kripto paraların fiyatlarını filtreleyin ve güncelleyin
    for coin in coins: 
        coin_id = coin["id"]
        coin_symbol = coin["kripto_adi"] + "USDT"

        if coin_symbol in all_prices:  #coin_symbol all_priceste var mı
            current_price = all_prices[coin_symbol]
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')

            # Fiyatı ve zamanı güncelle
            cursor.execute(
                "UPDATE 'Kripto Para' SET guncel_fiyat = ?, guncellenme_zamani = ? WHERE id = ?",
                (current_price, current_time, coin_id)
            )
            print(f"{coin_symbol} fiyatı güncellendi: {current_price}")

    conn.commit() #değişiklkleri kaydet
    conn.close()

# Veritabanındaki tüm dövizlerin fiyatlarını güncelle
def update_currency_prices():
    all_rates = get_all_currency_rates()
    if not all_rates:
        print("Döviz kurları alınamadı.")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tüm dövizleri seç
    cursor.execute("SELECT id, döviz_adi FROM 'Döviz'")
    currencies = cursor.fetchall()

    # Tüm döviz kurlarını filtreleyin ve güncelleyin
    for currency in currencies:
        currency_id = currency["id"]
        currency_name = currency["döviz_adi"]

        if currency_name in all_rates:
            current_price_in_tl = all_rates[currency_name]
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')

            # Fiyatı ve zamanı güncelle
            cursor.execute(
                "UPDATE 'Döviz' SET guncel_fiyat = ?, guncellenme_zamani = ? WHERE id = ?",
                (current_price_in_tl, current_time, currency_id)
            )
            print(f"{currency_name} fiyatı (1 birim kaç TL): {current_price_in_tl}")

    conn.commit()
    conn.close()

# Her 30 dakikada bir kripto ve döviz fiyatlarını güncelle
def start_price_updater():
    update_count = 0
    while True:
        update_crypto_prices()
        update_currency_prices()
        update_count += 1

        # Her iki güncellemeden sonra (yani her saat başı) fiyatları geçmiş tablolara kaydet
        if update_count % 2 == 0:
            save_prices_to_history()

        time.sleep(30)  # 30 dakika bekle

# Kripto ve döviz fiyatlarını geçmiş tablolara kaydet
def save_prices_to_history():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Kripto fiyatlarını geçmiş tabloya ekle
    cursor.execute("SELECT id, guncel_fiyat FROM 'Kripto Para'")
    kripto_prices = cursor.fetchall()

    for kripto in kripto_prices:
        kripto_id = kripto["id"]
        price = kripto["guncel_fiyat"]
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO 'Kripto_Gecmis' (kripto_id, fiyat, tarih) VALUES (?, ?, ?)",
            (kripto_id, price, current_time)
        )

    # Döviz fiyatlarını geçmiş tabloya ekle
    cursor.execute("SELECT id, guncel_fiyat FROM 'Döviz'")
    currency_prices = cursor.fetchall()

    for currency in currency_prices:
        currency_id = currency["id"]
        price = currency["guncel_fiyat"]
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO 'Döviz_Gecmis' (döviz_id, fiyat, tarih) VALUES (?, ?, ?)",
            (currency_id, price, current_time)
        )

    conn.commit()
    conn.close()
    print("Fiyatlar geçmiş tablolara kaydedildi.")