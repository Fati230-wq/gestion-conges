import sqlite3

# 🔗 إنشاء الاتصال بقاعدة البيانات
conn = sqlite3.connect('conges.db')
cur = conn.cursor()

# 🧱 إنشاء جدول الموظفين
cur.execute('''
    CREATE TABLE IF NOT EXISTS employes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL UNIQUE
    )
''')

# 🧱 إنشاء جدول العطل
cur.execute('''
    CREATE TABLE IF NOT EXISTS conges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employe_id INTEGER NOT NULL,
        date_debut TEXT NOT NULL,
        date_fin TEXT NOT NULL,
        FOREIGN KEY (employe_id) REFERENCES employes(id)
    )
''')

# 👥 لائحة الموظفين
employes = [
    'Achbani', 'Assamoum', 'Qadri', 'Fahdaoui',
    'El bejjaj', 'Guenani', 'Najah', 'Ibnass'
]

# ➕ إدخال الموظفين بدون تكرار
cur.executemany(
    'INSERT OR IGNORE INTO employes (nom) VALUES (?)',
    [(nom,) for nom in employes]
)

# 💾 حفظ التغييرات
conn.commit()
conn.close()

print("✅ Base de données 'conges.db' créée avec succès.")








