import sqlite3
import numpy as np
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# -------------------- دوال مساعدة --------------------
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """إنشاء الجداول وإضافة بيانات افتراضية إذا كانت فارغة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # جداول المراجع
    cursor.execute('''CREATE TABLE IF NOT EXISTS Departments
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Services
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Systems
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS RequestVia
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Holidays
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT UNIQUE NOT NULL)''')
    
    # جدول الطلبات الرئيسي
    cursor.execute('''CREATE TABLE IF NOT EXISTS Requests
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       department TEXT NOT NULL,
                       service TEXT NOT NULL,
                       system TEXT NOT NULL,
                       request_via TEXT NOT NULL,
                       receive_date TEXT NOT NULL,
                       response_date TEXT,
                       details TEXT,
                       receiver TEXT NOT NULL,
                       work_days INTEGER)''')
    
    # بيانات افتراضية للجداول المرجعية إذا كانت فارغة
    if not cursor.execute("SELECT 1 FROM Departments LIMIT 1").fetchone():
        cursor.executemany("INSERT INTO Departments (name) VALUES (?)", 
                           [("مديرية التربية",), ("مدرسة اليرموك",), ("قسم التقنيات",), ("مدرسة الأندلس",)])
        cursor.executemany("INSERT INTO Services (name) VALUES (?)",
                           [("صيانة أجهزة",), ("ترقية نظام",), ("تدريب",), ("استشارات",)])
        cursor.executemany("INSERT INTO Systems (name) VALUES (?)",
                           [("نظام نور",), ("نظام المراسلات",), ("البريد الإلكتروني",), ("نظام الموارد",)])
        cursor.executemany("INSERT INTO RequestVia (name) VALUES (?)",
                           [("بريد إلكتروني",), ("نظام المراسلات",), ("نور",)])
        # نموذج طلب تجريبي
        cursor.execute('''INSERT INTO Requests 
                          (department, service, system, request_via, receive_date, response_date, details, receiver, work_days)
                          VALUES (?,?,?,?,?,?,?,?,?)''',
                       ("مديرية التربية", "صيانة أجهزة", "نظام نور", "بريد إلكتروني",
                        "2026-04-20", "2026-04-25", "طلب صيانة عاجل", "أحمد محمد", 4))
    
    conn.commit()
    conn.close()

def get_holidays_list():
    """إرجاع قائمة تواريخ الإجازات بصيغة YYYY-MM-DD"""
    conn = get_db_connection()
    rows = conn.execute("SELECT date FROM Holidays").fetchall()
    conn.close()
    return [row['date'] for row in rows]

def calculate_workdays(start_date_str, end_date_str=None):
    """حساب أيام العمل بين تاريخين مع استبعاد الجمعة والسبت والإجازات"""
    if not end_date_str or end_date_str.strip() == "":
        return 0
    start = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    if end < start:
        end = start
    holidays = get_holidays_list()
    workdays = np.busday_count(start, end, weekmask='1111100', holidays=holidays)
    return int(workdays)

def get_table_data(table_name):
    """استرجاع جميع صفوف الجدول (id, name) مرتبة حسب الاسم"""
    conn = get_db_connection()
    rows = conn.execute(f"SELECT id, name FROM {table_name} ORDER BY name").fetchall()
    conn.close()
    return rows

# -------------------- Routes --------------------
@app.route('/')
def index():
    conn = get_db_connection()
    requests = conn.execute("SELECT * FROM Requests ORDER BY receive_date DESC").fetchall()
    conn.close()
    departments = get_table_data('Departments')
    services = get_table_data('Services')
    systems = get_table_data('Systems')
    request_via = get_table_data('RequestVia')
    return render_template('index.html',
                           requests=requests,
                           departments=departments,
                           services=services,
                           systems=systems,
                           request_via=request_via)

@app.route('/add_request', methods=['POST'])
def add_request():
    department = request.form['department']
    service = request.form['service']
    system = request.form['system']
    request_via = request.form['request_via']
    receive_date = request.form['receive_date']
    response_date = request.form.get('response_date', '')
    details = request.form['details']
    receiver = request.form['receiver']
    work_days = calculate_workdays(receive_date, response_date)
    conn = get_db_connection()
    conn.execute('''INSERT INTO Requests 
                    (department, service, system, request_via, receive_date, response_date, details, receiver, work_days)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
                 (department, service, system, request_via, receive_date,
                  response_date if response_date else None, details, receiver, work_days))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'تم إضافة الطلب بنجاح'})

@app.route('/calculate_workdays')
def calc_workdays_ajax():
    start = request.args.get('start')
    end = request.args.get('end')
    if not start or not end:
        return jsonify({'workdays': 0})
    days = calculate_workdays(start, end)
    return jsonify({'workdays': days})

@app.route('/admin')
def admin():
    departments = get_table_data('Departments')
    services = get_table_data('Services')
    systems = get_table_data('Systems')
    request_via = get_table_data('RequestVia')
    holidays = get_table_data('Holidays')
    return render_template('admin.html',
                           departments=departments,
                           services=services,
                           systems=systems,
                           request_via=request_via,
                           holidays=holidays)

@app.route('/add_item/<table_name>', methods=['POST'])
def add_item(table_name):
    name = request.form['name'].strip()
    if not name:
        return jsonify({'success': False, 'message': 'الاسم مطلوب'})
    try:
        conn = get_db_connection()
        conn.execute(f"INSERT INTO {table_name} (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'تمت الإضافة'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'العنصر موجود بالفعل'})

@app.route('/add_multiple_items/<table_name>', methods=['POST'])
def add_multiple_items(table_name):
    raw = request.form['items'].strip()
    if not raw:
        return jsonify({'success': False, 'message': 'لا توجد بيانات'})
    items = [item.strip() for item in raw.replace('\r', '').replace('\n', ',').split(',') if item.strip()]
    conn = get_db_connection()
    added = 0
    for name in items:
        try:
            conn.execute(f"INSERT INTO {table_name} (name) VALUES (?)", (name,))
            added += 1
        except:
            pass
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'تم إضافة {added} عنصر جديد'})

@app.route('/delete_item/<table_name>/<int:item_id>', methods=['DELETE'])
def delete_item(table_name, item_id):
    conn = get_db_connection()
    conn.execute(f"DELETE FROM {table_name} WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'تم الحذف'})

@app.route('/get_select_data')
def get_select_data():
    return jsonify({
        'departments': [{'id': r['id'], 'name': r['name']} for r in get_table_data('Departments')],
        'services': [{'id': r['id'], 'name': r['name']} for r in get_table_data('Services')],
        'systems': [{'id': r['id'], 'name': r['name']} for r in get_table_data('Systems')],
        'request_via': [{'id': r['id'], 'name': r['name']} for r in get_table_data('RequestVia')]
    })

@app.route('/get_statistics')
def get_statistics():
    conn = get_db_connection()
    stats = conn.execute('''SELECT receiver, COUNT(*) as count 
                            FROM Requests GROUP BY receiver ORDER BY count DESC''').fetchall()
    total = conn.execute('SELECT COUNT(*) as total FROM Requests').fetchone()['total']
    conn.close()
    return jsonify({'stats': [{'receiver': s['receiver'], 'count': s['count']} for s in stats],
                    'total': total})

@app.route('/filter_requests')
def filter_requests():
    receiver = request.args.get('receiver', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    department = request.args.get('department', '').strip()
    base_query = "SELECT * FROM Requests WHERE 1=1"
    params = []
    if receiver:
        base_query += " AND receiver = ?"
        params.append(receiver)
    if department:
        base_query += " AND department = ?"
        params.append(department)
    if date_from:
        base_query += " AND receive_date >= ?"
        params.append(date_from)
    if date_to:
        base_query += " AND receive_date <= ?"
        params.append(date_to)
    base_query += " ORDER BY receive_date DESC"
    conn = get_db_connection()
    rows = conn.execute(base_query, params).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

# -------------------- تشغيل التطبيق --------------------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8080, debug=True)
