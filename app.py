from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# Connexion à la base de données
def get_db_connection():
    conn = sqlite3.connect('conges.db')
    conn.row_factory = sqlite3.Row
    return conn

# Compter les jours ouvrables entre deux dates
def business_days(start_date, end_date):
    day_count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() not in (5, 6):  # Samedi et dimanche
            day_count += 1
        current += timedelta(days=1)
    return day_count

# Vérification des règles métier
def check_conditions(employe_id, date_debut, date_fin):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT nom FROM employes WHERE id = ?', (employe_id,))
    employe_name = cur.fetchone()['nom']

    cur.execute('SELECT e.nom, c.date_debut, c.date_fin FROM conges c JOIN employes e ON c.employe_id = e.id')
    conges = cur.fetchall()

    start = datetime.strptime(date_debut, "%Y-%m-%d")
    end = datetime.strptime(date_fin, "%Y-%m-%d")

    week_start = (start - timedelta(days=start.weekday())).date()
    week_end = week_start + timedelta(days=6)

    same_week_count = 0

    for conge in conges:
        nom = conge['nom']
        db_start = datetime.strptime(conge['date_debut'], "%Y-%m-%d")
        db_end = datetime.strptime(conge['date_fin'], "%Y-%m-%d")

        # Règle 1: Assamoum et Achbani ne peuvent pas être en congé en même temps
        if employe_name in ['Assamoum', 'Achbani'] and nom in ['Assamoum', 'Achbani']:
            if (start <= db_end and end >= db_start):
                conn.close()
                return False, "❌ Assamoum et Achbani ne peuvent pas prendre des congés en même temps."

        # Règle 2: Délai minimum entre congés pour Assamoum et Qadri
        if employe_name in ['Assamoum', 'Qadri'] and nom == employe_name:
            if db_end < start:
                gap = business_days(db_end + timedelta(days=1), start - timedelta(days=1))
                if gap <= 3:
                    conn.close()
                    return False, "❌ Le délai entre deux congés doit être supérieur à 3 jours."
            elif db_start > end:
                gap = business_days(end + timedelta(days=1), db_start - timedelta(days=1))
                if gap <= 3:
                    conn.close()
                    return False, "❌ Le délai entre deux congés doit être supérieur à 3 jours."

        # Règle 3: Pas plus de 5 employés (hors Fahdaoui et Najah) en congé la même semaine
        if db_start.date() <= week_end and db_end.date() >= week_start:
            if nom not in ['Fahdaoui', 'Najah']:
                same_week_count += 1

    if employe_name not in ['Fahdaoui', 'Najah'] and same_week_count >= 5:
        conn.close()
        return False, "❌ Il ne peut pas y avoir plus de 5 employés en congé durant la même semaine."

    conn.close()
    return True, ""

# Page d'accueil
@app.route('/')
def show_home():
    conn = get_db_connection()
    employes = conn.execute('SELECT id, nom FROM employes').fetchall()
    conn.close()
    return render_template('index.html', employes=employes, message=None)

# Ajouter un congé
@app.route('/add_conge', methods=['POST'])
def add_conge():
    conn = get_db_connection()
    cur = conn.cursor()

    employe_id = request.form['employe_id']
    date_debut = request.form['date_debut']
    date_fin = request.form['date_fin']

    is_valid, error_message = check_conditions(employe_id, date_debut, date_fin)

    if is_valid:
        cur.execute('INSERT INTO conges (employe_id, date_debut, date_fin) VALUES (?, ?, ?)',
                    (employe_id, date_debut, date_fin))
        conn.commit()
        message = "✅ Demande acceptée."
    else:
        message = error_message

    conn.close()
    conn = get_db_connection()
    employes = conn.execute('SELECT id, nom FROM employes').fetchall()
    conn.close()
    return render_template('index.html', employes=employes, message=message)

# Calendrier interactif
@app.route('/calendar_2025')
def calendar_2025():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT c.date_debut, c.date_fin, e.id as emp_id, e.nom FROM conges c JOIN employes e ON c.employe_id = e.id')
    conges = cur.fetchall()
    conn.close()

    conge_map = {}
    employe_noms = {}
    for conge in conges:
        start_date = datetime.strptime(conge['date_debut'], "%Y-%m-%d")
        end_date = datetime.strptime(conge['date_fin'], "%Y-%m-%d")
        emp_id = conge['emp_id']
        employe_noms[emp_id] = conge['nom']
        current = start_date
        while current <= end_date:
            if current.year == 2025:
                conge_map[current.strftime("%Y-%m-%d")] = emp_id
            current += timedelta(days=1)

    couleurs = {
        1: "#e74c3c", 2: "#3498db", 3: "#2ecc71", 4: "#f39c12",
        5: "#9b59b6", 6: "#1abc9c", 7: "#d35400", 8: "#7f8c8d"
    }

    return render_template('calendar_2025.html',
                           conge_map=conge_map,
                           couleurs=couleurs,
                           employe_noms=employe_noms,
                           date=datetime)

# Supprimer un congé
@app.route('/delete_conge_by_date', methods=['POST'])
def delete_conge_by_date():
    data = request.get_json()
    date = data.get('date')

    if not date:
        return jsonify({'success': False, 'message': 'Date manquante'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM conges WHERE date_debut = ? OR date_fin = ?', (date, date))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

# Formulaire d'inscription
@app.route('/register_employe')
def register_employe():
    return render_template('register_employe.html')

@app.route('/add_employe', methods=['POST'])
def add_employe():
    nom = request.form['nom']
    if nom:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO employes (nom) VALUES (?)', (nom,))
        conn.commit()
        conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
