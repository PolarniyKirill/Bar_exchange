import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, send_file
import database
import pandas as pd
from io import BytesIO

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/')
def index():
    try:
        drinks = database.get_drinks()
        return render_template('index.html', drinks=drinks)
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return "Ошибка при загрузке меню", 500

@app.route('/update/<drink_name>')
def update(drink_name):
    try:
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
        database.reset_prices()
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in reset: {e}")
        return "Ошибка при сбросе цен", 500

@app.route('/generate_report')
def generate_report():
    try:
        sales_data, total_revenue = database.generate_report()
        
        # Создаем DataFrame для отчета
        if sales_data:
            df = pd.DataFrame(sales_data, columns=['Название', 'Количество', 'Средняя стоимость', 'Общая выручка'])
            df.loc[len(df)] = ['Итого', '', '', total_revenue]
        else:
            df = pd.DataFrame(columns=['Название', 'Количество', 'Средняя стоимость', 'Общая выручка'])
            df.loc[0] = ['Итого', '', '', total_revenue]
        
        # Сохраняем DataFrame в файл Excel
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Отчет', index=False)
        writer.save()
        output.seek(0)
        
        return send_file(output, attachment_filename='report.xlsx', as_attachment=True)
    except Exception as e:
        logger.error(f"Error in generate_report: {e}")
        return "Ошибка при создании отчета", 500

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

if __name__ == '__main__':
    try:
        database.init_db()
        app.run(debug=True)
    except Exception as e:
        logger.error(f"Error starting app: {e}")