import sqlite3
import logging

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
        
        # Создаем таблицу orders, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drink_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        
        # Получаем все продажи с количеством и суммой выручки
        cursor.execute('''
            SELECT d.name, SUM(s.quantity), SUM(s.quantity * s.price)
            FROM sales s
            JOIN drinks d ON s.drink_id = d.id
            GROUP BY d.name
        ''')
        sales_data = cursor.fetchall()
        logger.debug(f"Sales data fetched: {sales_data}")
        
        # Получаем общую выручку и общее количество проданных напитков
        cursor.execute('''
            SELECT SUM(quantity), SUM(quantity * price) FROM sales
        ''')
        totals = cursor.fetchone()
        total_quantity = totals[0] if totals[0] is not None else 0
        total_revenue = totals[1] if totals[1] is not None else 0
        logger.debug(f"Total quantity fetched: {total_quantity}")
        logger.debug(f"Total revenue fetched: {total_revenue}")
        
        conn.close()
        
        return sales_data, total_quantity, total_revenue
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return [], 0, 0

def clear_sales():
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sales")
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error clearing sales: {e}")

def delete_drink(drink_name):
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        # Удаляем все записи продаж для данного напитка
        cursor.execute("SELECT id FROM drinks WHERE name = ?", (drink_name,))
        drink = cursor.fetchone()
        if drink:
            drink_id = drink[0]
            cursor.execute("DELETE FROM sales WHERE drink_id = ?", (drink_id,))
            
            # Удаляем сам напиток
            cursor.execute("DELETE FROM drinks WHERE name = ?", (drink_name,))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error deleting drink: {e}")

def update_drink(old_name, new_name, new_initial_price):
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        # Обновляем название и изначальную цену напитка
        cursor.execute("UPDATE drinks SET name = ?, initial_price = ?, current_price = ? WHERE name = ?", 
                       (new_name, new_initial_price, new_initial_price, old_name))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error updating drink: {e}")

def create_order(order_items):
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        for item in order_items:
            cursor.execute("INSERT INTO orders (drink_name, quantity, total_price) VALUES (?, ?, ?)", 
                           (item['name'], item['quantity'], item['total_price']))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error creating order: {e}")

def get_current_prices():
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, current_price FROM drinks")
        drinks = cursor.fetchall()
        
        conn.close()
        return drinks
    except Exception as e:
        logger.error(f"Error getting current prices: {e}")
        return []