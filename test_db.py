import sqlite3

conn = sqlite3.connect('conges.db')
c = conn.cursor()

print("📋 Liste des employés:")
employes = c.execute("SELECT * FROM employes").fetchall()
for e in employes:
    print(f"ID: {e[0]} | Nom: {e[1]} | Jours disponibles: {e[2]}")

print("\n📅 Liste des congés (avec noms):")
query = '''
SELECT conges.id, employes.nom, conges.date_debut, conges.date_fin
FROM conges
JOIN employes ON conges.employe_id = employes.id
'''
conges = c.execute(query).fetchall()
for cng in conges:
    print(f"ID: {cng[0]} | Employé: {cng[1]} | Du: {cng[2]} au {cng[3]}")

conn.close()

