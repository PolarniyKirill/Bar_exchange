import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, send_file, session
import database
import pandas as pd
from io import BytesIO
import sqlite3  # Импортируем sqlite3

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = 'supersecretkey'  # Нужен для работы сессий

@app.route('/')
def index():
    try:
        drinks = database.get_drinks()
        return render_template('index.html', drinks=drinks)
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return "Ошибка при загрузке меню", 500

@app.route('/update/<drink_name>', methods=['GET'])
def update(drink_name):
    try:
        # Записываем продажу напитка в таблицу sales
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        # Получаем текущую цену напитка
        cursor.execute("SELECT id, current_price FROM drinks WHERE name = ?", (drink_name,))
        drink = cursor.fetchone()
        if drink:
            drink_id = drink[0]
            current_price = drink[1]
            
            # Записываем продажу с количеством 1 и текущей ценой
            cursor.execute("INSERT INTO sales (drink_id, quantity, price) VALUES (?, ?, ?)", (drink_id, 1, current_price))
            conn.commit()
        
        conn.close()
        
        # Обновляем цены
        database.update_prices(drink_name)
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in update: {e}")
        return "Ошибка при обновлении цен", 500

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            name = request.form['name']
            initial_price = float(request.form['initial_price'])
            database.add_drink(name, initial_price)
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error in add POST: {e}")
            return "Ошибка при добавлении напитка", 500
    return render_template('add.html')

@app.route('/reset')
def reset():
    try:
        # Сбрасываем цены на изначальные значения
        database.reset_prices()
        
        # Очищаем таблицу sales
        database.clear_sales()
        
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in reset: {e}")
        return "Ошибка при сбросе цен", 500

@app.route('/generate_report')
def generate_report():
    try:
        sales_data, total_quantity, total_revenue = database.generate_report()
        logger.debug(f"Sales data from DB: {sales_data}")
        logger.debug(f"Total quantity from DB: {total_quantity}")
        logger.debug(f"Total revenue from DB: {total_revenue}")
        
        # Создаем DataFrame для отчета
        if sales_data:
            df = pd.DataFrame(sales_data, columns=['Название', 'Количество проданного', 'Сумма выручки'])
            # Преобразуем количественные значения в числовой формат
            df['Количество проданного'] = df['Количество проданного'].apply(lambda x: int(x) if x != '' else '')
            df['Сумма выручки'] = df['Сумма выручки'].apply(lambda x: round(float(x), 2) if x != '' else '')
            # Добавляем строку "Итого"
            df.loc[len(df)] = ['Итого', total_quantity, round(total_revenue, 2)]
        else:
            df = pd.DataFrame(columns=['Название', 'Количество проданного', 'Сумма выручки'])
            df.loc[0] = ['Итого', '', round(total_revenue, 2)]
        
        logger.debug(f"DataFrame created: {df}")
        
        # Сохраняем DataFrame в файл Excel
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Отчет', index=False)
        writer.close()  # Используем close вместо save
        output.seek(0)
        
        logger.debug("Excel file generated successfully")
        
        return send_file(output, download_name='report.xlsx', as_attachment=True)  # Используем download_name вместо attachment_filename
    except Exception as e:
        logger.error(f"Error in generate_report: {e}")
        return "Ошибка при создании отчета", 500

@app.route('/delete/<drink_name>')
def delete(drink_name):
    try:
        database.delete_drink(drink_name)
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in delete: {e}")
        return "Ошибка при удалении напитка", 500

@app.route('/edit/<old_name>', methods=['GET', 'POST'])
def edit(old_name):
    if request.method == 'POST':
        try:
            new_name = request.form['name']
            new_initial_price = float(request.form['initial_price'])
            database.update_drink(old_name, new_name, new_initial_price)
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error in edit POST: {e}")
            return "Ошибка при изменении напитка", 500
    try:
        drinks = database.get_drinks()
        drink = next((d for d in drinks if d[1] == old_name), None)
        if drink:
            return render_template('edit.html', drink=drink)
        else:
            return "Напиток не найден", 404
    except Exception as e:
        logger.error(f"Error in edit GET: {e}")
        return "Ошибка при загрузке формы редактирования", 500

@app.route('/api/drinks')
def api_drinks():
    try:
        drinks = database.get_drinks()
        drinks_list = [{'id': drink[0], 'name': drink[1], 'initial_price': drink[2], 'current_price': drink[3]} for drink in drinks]
        return jsonify(drinks_list)
    except Exception as e:
        logger.error(f"Error in API drinks: {e}")
        return jsonify([]), 500

@app.route('/client.html')
def client():
    return send_from_directory('.', 'client.html')

@app.route('/new_order')
def new_order():
    try:
        drinks = database.get_drinks()
        session['order'] = []  # Инициализируем пустой заказ в сессии
        return render_template('new_order.html', drinks=drinks)
    except Exception as e:
        logger.error(f"Error in new_order: {e}")
        return "Ошибка при создании нового заказа", 500

@app.route('/add_to_order/<drink_name>', methods=['GET'])
def add_to_order(drink_name):
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        # Получаем текущую цену напитка
        cursor.execute("SELECT id, current_price FROM drinks WHERE name = ?", (drink_name,))
        drink = cursor.fetchone()
        if drink:
            drink_id = drink[0]
            current_price = drink[1]
            
            # Получаем данные заказа из сессии
            order = session.get('order', [])
            existing_item = next((item for item in order if item['name'] == drink_name), None)
            
            if existing_item:
                # Увеличиваем количество и пересчитываем общую стоимость
                existing_item['quantity'] += 1
                existing_item['total_price'] = existing_item['price'] * existing_item['quantity']
            else:
                # Добавляем новый элемент в заказ
                order.append({
                    'name': drink_name,
                    'price': current_price,
                    'quantity': 1,
                    'total_price': current_price
                })
            
            session['order'] = order
        
        conn.close()
        return redirect(url_for('order_summary'))
    except Exception as e:
        logger.error(f"Error in add_to_order: {e}")
        return "Ошибка при добавлении напитка в заказ", 500

@app.route('/remove_from_order/<drink_name>', methods=['GET'])
def remove_from_order(drink_name):
    try:
        order = session.get('order', [])
        updated_order = []
        for item in order:
            if item['name'] == drink_name:
                if item['quantity'] > 1:
                    item['quantity'] -= 1
                    item['total_price'] = item['price'] * item['quantity']
                    updated_order.append(item)
            else:
                updated_order.append(item)
        
        session['order'] = updated_order
        return redirect(url_for('order_summary'))
    except Exception as e:
        logger.error(f"Error in remove_from_order: {e}")
        return "Ошибка при удалении напитка из заказа", 500

@app.route('/pay_order', methods=['POST'])
def pay_order():
    try:
        order = session.get('order', [])
        if order:
            # Сохраняем заказ в базе данных
            database.create_order(order)
            # Очищаем заказ в сессии
            session['order'] = []
        
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in pay_order: {e}")
        return "Ошибка при оплате заказа", 500

@app.route('/order_summary')
def order_summary():
    try:
        order = session.get('order', [])
        total_sum = sum(item['total_price'] for item in order)
        return render_template('order_summary.html', order=order, total_sum=round(total_sum, 2))
    except Exception as e:
        logger.error(f"Error in order_summary: {e}")
        return "Ошибка при подведении итога заказа", 500

if __name__ == '__main__':
    try:
        database.init_db()
        app.run(debug=True)
    except Exception as e:
        logger.error(f"Error starting app: {e}")