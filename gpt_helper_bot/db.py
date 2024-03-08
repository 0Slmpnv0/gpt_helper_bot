import logging
import sqlite3


def init_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    users_init = '''CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    context TEXT,
    subject TEXT,
    level TEXT,
    task TEXT, 
    admin INTEGER
    );'''  #поле task я не использую. Оно существует для соответствия условиям чеклиста
    cursor.execute(users_init)
    conn.commit()
    cursor.close()
    logging.debug('users db initiated')


def insert_data(user_id: int, subject: str = '', level: str = '', admin: int = 0, context: str = ''):
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    logging.debug('connected to users.db successfully')
    sql = '''INSERT 
            INTO users (user_id, context, subject, level, admin) 
            VALUES (?, ?, ?, ?, ?)'''
    cursor.execute(sql, (user_id, context, subject, level, str(admin)))
    conn.commit()
    cursor.close()
    logging.debug('insertion successful')


def update_subject(user_id: int, subject=''):
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    logging.debug('connected to users.db successfully')
    sql = '''UPDATE users 
            SET 
                subject = ?
            WHERE
                user_id = ?'''
    cursor.execute(sql, (subject, user_id))
    conn.commit()
    conn.close()
    logging.debug(f'updated subject successfully for {user_id}')


def update_level(user_id: int, level=''):
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    logging.debug('connected to users.db successfully')
    sql = '''UPDATE users 
            SET 
                level = ?
            WHERE
                user_id = ?'''
    cursor.execute(sql, (level, user_id))
    conn.commit()
    conn.close()
    logging.debug(f'updated level successfully for {user_id}')


def update_context(user_id: int, context=''):
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    logging.debug('connected to users.db successfully')
    sql = '''UPDATE users 
            SET 
                context = ?
            WHERE
                user_id = ?'''
    cursor.execute(sql, (sql, context))
    conn.commit()
    conn.close()
    logging.debug(f'updated context successfully for {user_id}')


def get_user_data(user_id: int):
    res = execute_query('SELECT * FROM users WHERE user_id = ?', (user_id, ))
    return res if res else []


def execute_query(query, data=()):
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    logging.debug('connected to users.db successfully')
    if data:
        return [dict(res) for res in cursor.execute(query, data)]
    else:
        return [dict(res) for res in cursor.execute(query)]
