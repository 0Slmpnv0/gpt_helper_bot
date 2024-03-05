import sqlite3
import random


def init_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    users_init = '''CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    context TEXT,
    subject TEXT,
    difficulty TEXT,
    admin INTEGER
    );'''
    cursor.execute(users_init)
    conn.commit()
    cursor.close()


def insert_data(user_id: str, subject: str = '', difficulty: str = '', admin: int = 0, context: str = ''):
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    sql = '''INSERT 
            INTO users (user_id, context, subject, difficulty, admin) 
            VALUES (?, ?, ?, ?, ?)'''
    cursor.execute(sql, (user_id, context, subject, difficulty, str(admin)))
    conn.commit()
    cursor.close()


def update_data(user_id: str, subject: str = '', difficulty: str = '', admin: int = 0, context: str = ''):
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    sql = '''UPDATE users 
            SET 
                context = ?,
                subject = ?,
                difficulty = ?,
                admin = ? 
            WHERE
                user_id = ?'''
    cursor.execute(sql, (context, subject, difficulty, admin, user_id))
    conn.commit()
    conn.close()


# Сделал лишнюю функцию для читабельности и красоты. Не знаю плохо это или хорошо, но удобно
def reset_data(user_id: str):
    update_data(user_id, subject='', difficulty='', context='')


def get_data(user_id: str):
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    sql = '''SELECT * FROM users WHERE user_id = ?'''
    conn.close()
    return cursor.execute(sql, user_id)


def select_from_users(param='*', where: tuple = ''):
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    sql = '''SELECT ? FROM users'''
    if where:
        sql += ' WHERE ? = ?'
    params = tuple(param) + where
    return cursor.execute(sql, params)
