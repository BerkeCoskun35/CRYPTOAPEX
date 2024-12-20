from pymongo import MongoClient

# MongoDB bağlantısını kuran fonksiyon
def get_db_connection():
    client = MongoClient('mongodb+srv://berkecoskun:Berke1035208@cluster0.ydrox.mongodb.net/')  # MongoDB'nin çalıştığı adres
    db = client['CryptoApex']  # Veritabanı adı
    return db

# Veritabanından kullanıcıları okuma
def select_in(db):
    users = db['users']
    for user in users.find():  # Tüm kullanıcıları al
        print(user)

# MongoDB bağlantısı alınıyor ve işlemler yapılıyor
db = get_db_connection()
select_in(db)