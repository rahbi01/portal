import sqlite3
import numpy as np
from datetime import datetime, date

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # إنشاء جدول الأقسام
    c.execute('''CREATE TABLE IF NOT EXISTS Departments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE)''')
    
    # إنشاء جدول الخدمات
    c.execute('''CREATE TABLE IF NOT EXISTS Services
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE)''')
    
    # إنشاء جدول الأنظمة
    c.execute('''CREATE TABLE IF NOT EXISTS Systems
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE)''')
    
    # إنشاء جدول وسائل الطلب
    c.execute('''CREATE TABLE IF NOT EXISTS RequestVia
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE)''')
    
    # إنشاء جدول الإجازات
    c.execute('''CREATE TABLE IF NOT EXISTS Holidays
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT NOT NULL UNIQUE)''')
    
    # إنشاء جدول الطلبات الرئيسي
    c.execute('''CREATE TABLE IF NOT EXISTS Requests
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
    
    # إضافة بيانات افتراضية للاختبار
    default_data(c)
    
    conn.commit()
    conn.close()
