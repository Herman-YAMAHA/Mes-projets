"""
main.py v2 - Point d'entree PharmGest.
Orchestre l'initialisation DB et le lancement GUI.
Dependances: pip install customtkinter matplotlib fpdf2
"""
from __future__ import annotations
import sys
from database import SQLiteDatabase
from gui import PharmacieApp

def main() -> None:
    db = SQLiteDatabase()
    try:
        db.initialiser()
        print("[OK] Base de données initialisée.")
    except RuntimeError as e:
        print(f"[ERREUR] {e}"); sys.exit(1)
    try:
        app = PharmacieApp(db)
        app.mainloop()
    except KeyboardInterrupt:
        print("\n[INFO] Interrompu.")
    except Exception as e:
        print(f"[ERREUR] {e}")
    finally:
        db.fermer()
        print("[OK] Base fermée.")

if __name__ == "__main__":
    main()
