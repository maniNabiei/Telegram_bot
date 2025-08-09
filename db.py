import sqlite3

def create_db():
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            is_verified INTEGER DEFAULT 0,
            is_logged_in INTEGER DEFAULT 0,
            tokens INTEGER DEFAULT 10
        )'''
    )
    conn.commit()
    conn.close()

def register_user(telegram_id, first_name, last_name, email, password):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('''INSERT INTO accounts 
        (telegram_id, first_name, last_name, email, password, is_verified, is_logged_in) 
        VALUES (?, ?, ?, ?, ?, 1, 1)''',
        (telegram_id, first_name, last_name, email, password)
    )
    conn.commit()
    conn.close()

def login_user(email, password, new_telegram_id):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute("SELECT * FROM accounts WHERE email = ? AND password = ?", (email, password))
    result = c.fetchone()
    if result:
        c.execute("UPDATE accounts SET telegram_id = ?, is_logged_in = 1 WHERE email = ?", (new_telegram_id, email))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def logout_user(telegram_id):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute("UPDATE accounts SET is_logged_in = 0 WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()

def is_logged_in(telegram_id):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute("SELECT is_logged_in FROM accounts WHERE telegram_id = ?", (telegram_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def get_tokens(telegram_id):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute("SELECT tokens FROM accounts WHERE telegram_id = ?", (telegram_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def decrement_token(telegram_id):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute("UPDATE accounts SET tokens = tokens - 1 WHERE telegram_id = ? AND tokens > 0", (telegram_id,))
    conn.commit()
    conn.close()
def add_tokens(telegram_id, count):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute("UPDATE accounts SET tokens = tokens + ? WHERE telegram_id = ?", (count, telegram_id))
    conn.commit()
    conn.close()

def get_email(telegram_id):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute("SELECT email FROM accounts WHERE telegram_id = ?", (telegram_id,))
    result = c.fetchone()
    conn.commit()
    conn.close()
    return result
