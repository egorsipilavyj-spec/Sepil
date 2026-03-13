import sqlite3

def get_db():
    conn = sqlite3.connect('sepil.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    # Таблица юзеров
    db.execute('''CREATE TABLE IF NOT EXISTS users 
                  (username TEXT PRIMARY KEY, nickname TEXT, password TEXT)''')
    # Таблица сообщений
    db.execute('''CREATE TABLE IF NOT EXISTS messages 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   sender TEXT, receiver TEXT, msg TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    db.commit()

init_db()