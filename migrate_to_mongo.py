import requests
import json
from datetime import datetime
from database import get_db_connection


def fetch_historical_ohlc(crypto_symbol, interval, start_date, end_date):
    """
    Binance API'den belirli bir kripto paranın belirli bir tarih aralığı için OHLC verilerini çeker.
    """
    url = "https://api.binance.com/api/v3/klines"
    start_time = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
    end_time = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)
    
    all_data = []
    while start_time < end_time:
        params = {
            "symbol": crypto_symbol,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1000
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Binance API isteği başarısız oldu ({crypto_symbol}): {response.status_code}, {response.text}")
            break
        
        data = response.json()
        if not data:
            print(f"{crypto_symbol} için veri bulunamadı.")
            break
        
        all_data.extend(data)
        start_time = data[-1][6] + 1  # Son alınan kaydın kapanış zamanı +1 ms

    return all_data


def fetch_and_save_ohlc_for_all_cryptos(start_date, end_date):
    """
    Veritabanındaki tüm kripto paralar için OHLC verilerini çeker ve JSON dosyasına kaydeder.
    """
    db = get_db_connection()
    crypto_collection = db["Kripto Para"]
    
    # Veritabanındaki tüm kripto paraları al
    crypto_list = [crypto["kripto_adi"] + "USDT" for crypto in crypto_collection.find()]
    
    interval = "1h"  # Saatlik veri
    all_ohlc_data = {}
    
    for crypto in crypto_list:
        print(f"{crypto} için veri çekiliyor...")
        ohlc_data = fetch_historical_ohlc(crypto, interval, start_date, end_date)
        if ohlc_data:
            all_ohlc_data[crypto] = [
                {
                    "open_time": datetime.utcfromtimestamp(item[0] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                    "open": float(item[1]),
                    "high": float(item[2]),
                    "low": float(item[3]),
                    "close": float(item[4])
                }
                for item in ohlc_data
            ]
        else:
            print(f"{crypto} için veri alınamadı.")
    
    # JSON formatında kaydet
    with open("all_crypto_hourly_ohlc.json", "w", encoding="utf-8") as json_file:
        json.dump(all_ohlc_data, json_file, ensure_ascii=False, indent=4)
    print("OHLC verileri all_crypto_hourly_ohlc.json dosyasına kaydedildi.")


# Kullanım
start_date = "2024-11-27"
end_date = "2024-12-19"
fetch_and_save_ohlc_for_all_cryptos(start_date, end_date)
