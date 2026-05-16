import sqlite3
from datetime import datetime
import os

DB_PATH = os.environ.get("DB_PATH", "bot_database.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 0,
        total_sent INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        is_muted INTEGER DEFAULT 0,
        mute_until INTEGER DEFAULT 0,
        registered_at TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS promocodes (
        code TEXT PRIMARY KEY,
        amount INTEGER,
        max_uses INTEGER DEFAULT 1,
        used_count INTEGER DEFAULT 0,
        created_by INTEGER,
        created_at TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS promo_uses (
        user_id INTEGER,
        code TEXT,
        used_at TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS mute_history (
        user_id INTEGER,
        admin_id INTEGER,
        duration INTEGER,
        reason TEXT,
        muted_at TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        method TEXT,
        status TEXT,
        created_at TEXT
    )
''')
conn.commit()

def register_user(user_id, username):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, username, registered_at) VALUES (?, ?, ?)",
                      (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else 0

def add_balance(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

def deduct_balance(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?", 
                   (amount, user_id, amount))
    conn.commit()
    return cursor.rowcount > 0

def add_to_sent(user_id, count=1):
    cursor.execute("UPDATE users SET total_sent = total_sent + ? WHERE user_id = ?", (count, user_id))
    conn.commit()

def is_banned(user_id):
    cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    return res and res[0] == 1

def is_muted(user_id):
    cursor.execute("SELECT is_muted, mute_until FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if res and res[0] == 1 and res[1] > 0:
        if datetime.now().timestamp() > res[1]:
            cursor.execute("UPDATE users SET is_muted = 0, mute_until = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            return False
        return True
    return False

def ban_user(user_id):
    cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()

def unban_user(user_id):
    cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()

def mute_user(user_id, admin_id, duration_minutes, reason=""):
    mute_until = int(datetime.now().timestamp() + duration_minutes * 60)
    cursor.execute("UPDATE users SET is_muted = 1, mute_until = ? WHERE user_id = ?", (mute_until, user_id))
    cursor.execute("INSERT INTO mute_history (user_id, admin_id, duration, reason, muted_at) VALUES (?, ?, ?, ?, ?)",
                   (user_id, admin_id, duration_minutes, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def unmute_user(user_id):
    cursor.execute("UPDATE users SET is_muted = 0, mute_until = 0 WHERE user_id = ?", (user_id,))
    conn.commit()

def create_promocode(amount, max_uses, created_by):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    cursor.execute("INSERT INTO promocodes (code, amount, max_uses, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
                   (code, amount, max_uses, created_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    return code

def use_promocode(user_id, code):
    cursor.execute("SELECT amount, max_uses, used_count FROM promocodes WHERE code = ?", (code,))
    promo = cursor.fetchone()
    if not promo:
        return False, "Промокод не найден"
    
    amount, max_uses, used_count = promo
    
    cursor.execute("SELECT * FROM promo_uses WHERE user_id = ? AND code = ?", (user_id, code))
    if cursor.fetchone():
        return False, "Вы уже использовали этот промокод"
    
    if used_count >= max_uses:
        return False, "Промокод больше недействителен"
    
    cursor.execute("UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?", (code,))
    cursor.execute("INSERT INTO promo_uses (user_id, code, used_at) VALUES (?, ?, ?)",
                   (user_id, code, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    add_balance(user_id, amount)
    conn.commit()
    return True, f"+{amount} сообщений"

def get_stats():
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(balance) FROM users")
    total_balance = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(total_sent) FROM users")
    total_sent = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
    banned_count = cursor.fetchone()[0]
    return total_users, total_balance, total_sent, banned_count