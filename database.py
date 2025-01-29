import sqlite3
import logging
import pandas as pd

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_db():
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        # Создаем таблицу drinks, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                initial_price REAL NOT NULL,
                current_price REAL NOT NULL
            )
        ''')
        
        # Проверяем, есть ли уже записи в таблице drinks
        cursor.execute("SELECT COUNT(*) FROM drinks")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Добавляем примерные напитки, если таблица пустая
            cursor.executemany('''
                INSERT INTO drinks (name, initial_price, current_price) VALUES (?, ?, ?)
            ''', [
                ('Пиво', 100, 100),
                ('Вино', 200, 200),
                ('Водка', 300, 300)
            ])
        
        # Создаем таблицу sales, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drink_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (drink_id) REFERENCES drinks(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error initializing DB: {e}")

def get_drinks():
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drinks")
        drinks = cursor.fetchall()
        conn.close()
        return drinks
    except Exception as e:
        logger.error(f"Error getting drinks: {e}")
        return []

def update_prices(chosen_drink):
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM drinks")
        drinks = cursor.fetchall()
        
        for drink in drinks:
            if drink[1] == chosen_drink:
                new_price = drink[3] * 1.04
            else:
                new_price = drink[3] * 0.98
            
            cursor.execute("UPDATE drinks SET current_price = ? WHERE id = ?", (new_price, drink[0]))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error updating prices: {e}")

def add_drink(name, initial_price):
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO drinks (name, initial_price, current_price) VALUES (?, ?, ?)", (name, initial_price, initial_price))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error adding drink: {e}")

def reset_prices():
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        cursor.execute("UPDATE drinks SET current_price = initial_price")
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error resetting prices: {e}")

def record_sale(drink_id, quantity, price):
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        cursor.execute("INSERT INTO sales (drink_id, quantity, price) VALUES (?, ?, ?)", (drink_id, quantity, price))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error recording sale: {e}")

def generate_report():
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        # Получаем все продажи
        cursor.execute('''
            SELECT d.name, SUM(s.quantity), AVG(s.price), SUM(s.quantity * s.price)
            FROM sales s
            JOIN drinks d ON s.drink_id = d.id
            GROUP BY d.name
        ''')
        sales_data = cursor.fetchall()
        
        # Получаем общую выручку
        cursor.execute('''
            SELECT SUM(quantity * price) FROM sales
        ''')
        total_revenue = cursor.fetchone()[0]
        if total_revenue is None:
            total_revenue = 0
        
        conn.close()
        
        return sales_data, total_revenue
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return [], 0