from pymongo import MongoClient

# MongoDB bağlantısını kuran fonksiyon
def get_db_connection():
    # MongoDB Atlas bağlantı URL'si
    url = "mongodb+srv://cryptoApex:<db_password>@cluster0.lyoac.mongodb.net/"
    client = MongoClient(url)  # Atlas'a bağlan
    db = client['json_to_mongo']  # Veritabanı adı
    return db

# Veritabanından kullanıcıları okuma
def select_in(db):
    users = db['users']  # 'users' koleksiyonunu seç
    for user in users.find():  # Tüm kullanıcıları al
        print(user)

# MongoDB bağlantısı alınıyor ve işlemler yapılıyor
db = get_db_connection()
select_in(db)
