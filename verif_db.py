import sqlite3
conn = sqlite3.connect("bookworld_final.db")
for (nom,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print("TABLE", nom)
    for col in conn.execute(f"PRAGMA table_info('{nom}')"):
        print("   ", col[1], col[2])   # nom de colonne, type