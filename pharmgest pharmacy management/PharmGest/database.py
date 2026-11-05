"""
database.py v4 — Persistance enrichie.
v4: stock par lot (quantite_restante), annulation vente, alertes peremption par lot,
    CA par periode, listing utilisateurs, suppression lots vides.
"""
from __future__ import annotations
import sqlite3, os, csv, shutil, json
from datetime import date, datetime, timedelta
from typing import Optional
from models import (Categorie, Produit, Utilisateur, Vente, Arrivage, MouvementStock, HistoriqueAction)

class SQLiteDatabase:
    DB_FILENAME: str = "pharmacie.db"

    def __init__(self, db_path: Optional[str]=None) -> None:
        self.__db_path: str = db_path or self.DB_FILENAME
        self.__conn: Optional[sqlite3.Connection] = None

    @property
    def db_path(self) -> str: return self.__db_path

    def initialiser(self) -> None:
        try:
            self.__conn = sqlite3.connect(self.__db_path)
            self.__conn.execute("PRAGMA foreign_keys = ON")
            self.__creer_tables(); self.__migrer_tables(); self.__inserer_defaut()
        except sqlite3.Error as e: raise RuntimeError(f"Init DB echouee: {e}") from e

    def fermer(self) -> None:
        try:
            if self.__conn: self.__conn.close()
        except: pass
        finally: self.__conn = None

    @property
    def connexion(self) -> sqlite3.Connection:
        if self.__conn is None: raise RuntimeError("DB non initialisee.")
        return self.__conn

    def __creer_tables(self) -> None:
        self.connexion.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY, nom TEXT NOT NULL, date_creation TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS produits (
                id TEXT PRIMARY KEY, nom TEXT NOT NULL, categorie_id TEXT NOT NULL,
                prix REAL NOT NULL CHECK(prix>=0), quantite INTEGER NOT NULL CHECK(quantite>=0),
                description TEXT DEFAULT '', date_expiration TEXT DEFAULT '',
                sur_ordonnance INTEGER DEFAULT 0, date_creation TEXT NOT NULL,
                FOREIGN KEY(categorie_id) REFERENCES categories(id));
            CREATE TABLE IF NOT EXISTS ventes (
                id TEXT PRIMARY KEY, client_nom TEXT DEFAULT '', montant_total REAL NOT NULL,
                lignes_json TEXT DEFAULT '[]', structure_hospitaliere TEXT DEFAULT '',
                date_vente TEXT NOT NULL, date_creation TEXT NOT NULL,
                produit_id TEXT DEFAULT '', produit_nom TEXT DEFAULT '',
                quantite INTEGER DEFAULT 0, prix_unitaire REAL DEFAULT 0,
                annulee INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL, is_admin INTEGER DEFAULT 0,
                security_question TEXT DEFAULT '', security_answer_hash TEXT DEFAULT '',
                must_change_password INTEGER DEFAULT 0, date_creation TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS arrivages (
                id TEXT PRIMARY KEY, produit_id TEXT NOT NULL, quantite INTEGER NOT NULL,
                quantite_restante INTEGER NOT NULL DEFAULT 0,
                fournisseur TEXT DEFAULT '', description TEXT DEFAULT '',
                date_peremption TEXT DEFAULT '',
                date_arrivage TEXT NOT NULL, date_creation TEXT NOT NULL,
                FOREIGN KEY(produit_id) REFERENCES produits(id));
            CREATE TABLE IF NOT EXISTS mouvements_stock (
                id TEXT PRIMARY KEY, produit_id TEXT NOT NULL, produit_nom TEXT DEFAULT '',
                type_mvt TEXT NOT NULL, quantite INTEGER NOT NULL,
                description TEXT DEFAULT '', date_mvt TEXT NOT NULL, date_creation TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS historique_actions (
                id TEXT PRIMARY KEY, utilisateur TEXT NOT NULL, action TEXT NOT NULL,
                description TEXT NOT NULL, cible TEXT DEFAULT '',
                date_action TEXT NOT NULL, date_creation TEXT NOT NULL);
        """)
        self.connexion.commit()

    def __migrer_tables(self) -> None:
        cur = self.connexion.cursor()
        try:
            cur.execute("PRAGMA table_info(produits)")
            cols = {r[1] for r in cur.fetchall()}
            if "sur_ordonnance" not in cols:
                cur.execute("ALTER TABLE produits ADD COLUMN sur_ordonnance INTEGER DEFAULT 0")

            cur.execute("PRAGMA table_info(utilisateurs)")
            cols2 = {r[1] for r in cur.fetchall()}
            if "is_admin" not in cols2:
                cur.execute("ALTER TABLE utilisateurs ADD COLUMN is_admin INTEGER DEFAULT 0")

            cur.execute("PRAGMA table_info(ventes)")
            cols3 = {r[1] for r in cur.fetchall()}
            for col,typ in [("lignes_json","TEXT DEFAULT '[]'"),("structure_hospitaliere","TEXT DEFAULT ''"),("annulee","INTEGER DEFAULT 0")]:
                if col not in cols3:
                    cur.execute(f"ALTER TABLE ventes ADD COLUMN {col} {typ}")

            cur.execute("PRAGMA table_info(arrivages)")
            cols4 = {r[1] for r in cur.fetchall()}
            if "date_peremption" not in cols4:
                cur.execute("ALTER TABLE arrivages ADD COLUMN date_peremption TEXT DEFAULT ''")
            if "quantite_restante" not in cols4:
                cur.execute("ALTER TABLE arrivages ADD COLUMN quantite_restante INTEGER NOT NULL DEFAULT 0")
                # Migration: quantite_restante = quantite pour les lots existants
                cur.execute("UPDATE arrivages SET quantite_restante=quantite WHERE quantite_restante=0")

            self.connexion.commit()
        except: self.connexion.rollback()

    def __inserer_defaut(self) -> None:
        cur = self.connexion.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM categories")
            if cur.fetchone()[0] == 0:
                for nom in ["Antibiotiques","Antalgiques","Anti-inflammatoires","Vitamines & Compléments",
                             "Dermatologie","Pédiatrie","Ophtalmologie","Divers"]:
                    c = Categorie(nom=nom)
                    cur.execute("INSERT INTO categories VALUES(?,?,?)", (c.id,nom,c.date_creation))
                self.connexion.commit()
        except: self.connexion.rollback()

    # ═══════════ CATEGORIES CRUD ═══════════
    def ajouter_categorie(self, c: Categorie) -> None:
        try:
            # Vérifier unicité du nom de catégorie
            cur = self.connexion.execute("SELECT COUNT(*) FROM categories WHERE LOWER(nom)=LOWER(?)", (c.nom,))
            if cur.fetchone()[0] > 0:
                raise ValueError(f"Une catégorie portant le nom « {c.nom} » existe déjà.")
            self.connexion.execute("INSERT INTO categories VALUES(?,?,?)", (c.id,c.nom,c.date_creation))
            self.connexion.commit()
        except ValueError: self.connexion.rollback(); raise
        except sqlite3.IntegrityError as e: self.connexion.rollback(); raise ValueError(str(e))
        except sqlite3.Error as e: self.connexion.rollback(); raise RuntimeError(str(e))

    def lister_categories(self) -> list[Categorie]:
        cur = self.connexion.execute("SELECT id,nom,date_creation FROM categories ORDER BY nom")
        return [Categorie.from_dict({"id":r[0],"nom":r[1],"date_creation":r[2]}) for r in cur.fetchall()]

    def modifier_categorie(self, c: Categorie) -> None:
        try:
            cur = self.connexion.execute("SELECT COUNT(*) FROM categories WHERE LOWER(nom)=LOWER(?) AND id!=?", (c.nom, c.id))
            if cur.fetchone()[0] > 0:
                raise ValueError(f"Une catégorie portant le nom « {c.nom} » existe déjà.")
            self.connexion.execute("UPDATE categories SET nom=? WHERE id=?", (c.nom, c.id))
            self.connexion.commit()
        except ValueError: self.connexion.rollback(); raise
        except sqlite3.Error as e: self.connexion.rollback(); raise RuntimeError(str(e))

    def supprimer_categorie(self, cid: str) -> None:
        cur = self.connexion.execute("SELECT COUNT(*) FROM produits WHERE categorie_id=?", (cid,))
        if cur.fetchone()[0] > 0:
            raise ValueError("Impossible de supprimer : des produits utilisent cette catégorie.")
        self.connexion.execute("DELETE FROM categories WHERE id=?", (cid,)); self.connexion.commit()

    # ═══════════ PRODUITS ═══════════
    def _row_to_produit(self, r) -> Produit:
        return Produit.from_dict({"id":r[0],"nom":r[1],"categorie_id":r[2],"prix":r[3],
            "quantite":r[4],"description":r[5],"date_expiration":r[6],
            "sur_ordonnance":r[7] if len(r)>7 else 0,"date_creation":r[8] if len(r)>8 else ""})

    _SEL_PROD = "SELECT id,nom,categorie_id,prix,quantite,description,date_expiration,sur_ordonnance,date_creation FROM produits"

    def ajouter_produit(self, p: Produit) -> None:
        d = p.to_dict()
        try:
            # Vérifier unicité du nom de produit
            cur = self.connexion.execute("SELECT COUNT(*) FROM produits WHERE LOWER(nom)=LOWER(?)", (d["nom"],))
            if cur.fetchone()[0] > 0:
                raise ValueError(f"Un produit portant le nom « {d['nom']} » existe déjà.")
            self.connexion.execute(
                "INSERT INTO produits(id,nom,categorie_id,prix,quantite,description,date_expiration,sur_ordonnance,date_creation) VALUES(?,?,?,?,?,?,?,?,?)",
                (d["id"],d["nom"],d["categorie_id"],d["prix"],d["quantite"],d["description"],d["date_expiration"],d["sur_ordonnance"],d["date_creation"]))
            self.connexion.commit()
        except ValueError: self.connexion.rollback(); raise
        except sqlite3.Error as e: self.connexion.rollback(); raise RuntimeError(str(e))

    def modifier_produit(self, p: Produit) -> None:
        d = p.to_dict()
        try:
            self.connexion.execute(
                "UPDATE produits SET nom=?,categorie_id=?,prix=?,quantite=?,description=?,date_expiration=?,sur_ordonnance=? WHERE id=?",
                (d["nom"],d["categorie_id"],d["prix"],d["quantite"],d["description"],d["date_expiration"],d["sur_ordonnance"],d["id"]))
            self.connexion.commit()
        except sqlite3.Error as e: self.connexion.rollback(); raise RuntimeError(str(e))

    def obtenir_produit(self, pid: str) -> Optional[Produit]:
        cur = self.connexion.execute(f"{self._SEL_PROD} WHERE id=?", (pid,))
        r = cur.fetchone()
        return self._row_to_produit(r) if r else None

    def lister_produits(self) -> list[Produit]:
        cur = self.connexion.execute(f"{self._SEL_PROD} ORDER BY nom")
        return [self._row_to_produit(r) for r in cur.fetchall()]

    def rechercher_produits(self, terme: str) -> list[Produit]:
        like = f"%{terme}%"
        cur = self.connexion.execute(
            f"{self._SEL_PROD} WHERE nom LIKE ? OR categorie_id IN (SELECT id FROM categories WHERE nom LIKE ?) ORDER BY nom",
            (like, like))
        return [self._row_to_produit(r) for r in cur.fetchall()]

    def filtrer_produits(self, terme:str="", categorie_id:str="", ordo:str="",
                         prix_min:float=0, prix_max:float=0,
                         qte_min:int=-1, qte_max:int=-1) -> list[Produit]:
        sql = f"{self._SEL_PROD} WHERE 1=1"
        params = []
        if terme:
            sql += " AND (nom LIKE ? OR categorie_id IN (SELECT id FROM categories WHERE nom LIKE ?))"
            params += [f"%{terme}%", f"%{terme}%"]
        if categorie_id:
            sql += " AND categorie_id=?"; params.append(categorie_id)
        if ordo == "oui":
            sql += " AND sur_ordonnance=1"
        elif ordo == "non":
            sql += " AND sur_ordonnance=0"
        if prix_min > 0:
            sql += " AND prix>=?"; params.append(prix_min)
        if prix_max > 0:
            sql += " AND prix<=?"; params.append(prix_max)
        if qte_min >= 0:
            sql += " AND quantite>=?"; params.append(qte_min)
        if qte_max >= 0:
            sql += " AND quantite<=?"; params.append(qte_max)
        sql += " ORDER BY nom"
        cur = self.connexion.execute(sql, params)
        return [self._row_to_produit(r) for r in cur.fetchall()]

    def supprimer_produit(self, pid: str) -> None:
        self.connexion.execute("DELETE FROM arrivages WHERE produit_id=?", (pid,))
        self.connexion.execute("DELETE FROM produits WHERE id=?", (pid,))
        self.connexion.commit()

    def produits_expires_ou_proches(self, jours: int = 30) -> list[Produit]:
        seuil = (date.today()+timedelta(days=jours)).isoformat()
        cur = self.connexion.execute(
            f"{self._SEL_PROD} WHERE date_expiration<=? AND date_expiration!='' ORDER BY date_expiration", (seuil,))
        return [self._row_to_produit(r) for r in cur.fetchall()]

    def arrivages_expires_ou_proches(self, jours: int = 30) -> list[dict]:
        """Retourne les lots (arrivages) expirés ou proches de péremption avec nom produit."""
        seuil = (date.today()+timedelta(days=jours)).isoformat()
        cur = self.connexion.execute(
            """SELECT a.id, a.produit_id, a.quantite, a.quantite_restante, a.fournisseur,
                      a.date_peremption, a.date_arrivage, p.nom as produit_nom
               FROM arrivages a JOIN produits p ON a.produit_id=p.id
               WHERE a.date_peremption<=? AND a.date_peremption!='' AND a.quantite_restante>0
               ORDER BY a.date_peremption""", (seuil,))
        result = []
        for r in cur.fetchall():
            try: jr = (date.fromisoformat(r[5])-date.today()).days
            except: jr = 9999
            result.append({"id":r[0],"produit_id":r[1],"quantite":r[2],"quantite_restante":r[3],
                           "fournisseur":r[4],"date_peremption":r[5],"date_arrivage":r[6],
                           "produit_nom":r[7],"jours_restants":jr,"est_perime":jr<0})
        return result

    def lots_perimes_non_vides(self) -> list[dict]:
        """Lots périmés avec stock > 0 pour notification."""
        today = date.today().isoformat()
        cur = self.connexion.execute(
            """SELECT a.id, a.produit_id, a.quantite_restante, a.date_peremption, p.nom
               FROM arrivages a JOIN produits p ON a.produit_id=p.id
               WHERE a.date_peremption<? AND a.date_peremption!='' AND a.quantite_restante>0
               ORDER BY a.date_peremption""", (today,))
        return [{"id":r[0],"produit_id":r[1],"quantite_restante":r[2],"date_peremption":r[3],"produit_nom":r[4]} for r in cur.fetchall()]

    def maj_description_produit_depuis_arrivages(self, produit_id: str) -> None:
        """Met a jour la description du produit avec le recap de ses lots actifs."""
        arrs = self.lister_arrivages(produit_id)
        if not arrs: return
        lignes = []
        for a in arrs:
            if a.quantite_restante > 0:
                dt = a.date_arrivage[:10]
                prem = a.date_peremption or "N/A"
                lignes.append(f"Lot {dt}: {a.quantite_restante} unites, exp: {prem} ({a.fournisseur})")
        desc = "\n".join(lignes) if lignes else "(tous les lots sont vides)"
        dates_futures = []
        for a in arrs:
            if a.date_peremption and a.quantite_restante > 0:
                try:
                    d = date.fromisoformat(a.date_peremption)
                    if d >= date.today(): dates_futures.append(d)
                except: pass
        exp_str = min(dates_futures).isoformat() if dates_futures else ""
        self.connexion.execute("UPDATE produits SET description=?, date_expiration=? WHERE id=?",
                               (desc, exp_str, produit_id))
        self.connexion.commit()

    def recalculer_stock_produit(self, produit_id: str) -> None:
        """Recalcule le stock global du produit = somme quantite_restante de TOUS les lots (y compris périmés)."""
        cur = self.connexion.execute(
            "SELECT COALESCE(SUM(quantite_restante),0) FROM arrivages WHERE produit_id=?",
            (produit_id,))
        total = cur.fetchone()[0]
        self.connexion.execute("UPDATE produits SET quantite=? WHERE id=?", (total, produit_id))
        self.connexion.commit()

    def stock_vendable(self, produit_id: str) -> int:
        """Stock vendable = somme quantite_restante des lots NON périmés."""
        today = date.today().isoformat()
        cur = self.connexion.execute(
            """SELECT COALESCE(SUM(quantite_restante),0) FROM arrivages
               WHERE produit_id=? AND quantite_restante>0
               AND (date_peremption>=? OR date_peremption='')""",
            (produit_id, today))
        return cur.fetchone()[0]

    def stock_perime(self, produit_id: str) -> int:
        """Stock périmé = somme quantite_restante des lots périmés."""
        today = date.today().isoformat()
        cur = self.connexion.execute(
            """SELECT COALESCE(SUM(quantite_restante),0) FROM arrivages
               WHERE produit_id=? AND quantite_restante>0
               AND date_peremption<? AND date_peremption!=''""",
            (produit_id, today))
        return cur.fetchone()[0]

    def stock_details(self, produit_id: str) -> dict:
        """Retourne stock total, stock périmé, stock vendable pour un produit."""
        total_cur = self.connexion.execute(
            "SELECT COALESCE(SUM(quantite_restante),0) FROM arrivages WHERE produit_id=?",
            (produit_id,))
        stock_total = total_cur.fetchone()[0]
        s_perime = self.stock_perime(produit_id)
        s_vendable = self.stock_vendable(produit_id)
        return {"stock_total": stock_total, "stock_perime": s_perime, "stock_vendable": s_vendable}

    def supprimer_lots_vides(self, produit_id: str) -> None:
        """Supprime les lots dont quantite_restante = 0."""
        self.connexion.execute("DELETE FROM arrivages WHERE produit_id=? AND quantite_restante=0", (produit_id,))
        self.connexion.commit()

    # ═══════════ VENTES ═══════════
    def ajouter_vente(self, v: Vente) -> None:
        d = v.to_dict()
        try:
            self.connexion.execute(
                "INSERT INTO ventes(id,client_nom,montant_total,lignes_json,structure_hospitaliere,date_vente,date_creation,produit_id,produit_nom,quantite,prix_unitaire,annulee) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (d["id"],d["client_nom"],d["montant_total"],d["lignes_json"],d["structure_hospitaliere"],d["date_vente"],d["date_creation"],d["produit_id"],d["produit_nom"],d["quantite"],d["prix_unitaire"],d["annulee"]))
            self.connexion.commit()
        except sqlite3.Error as e: self.connexion.rollback(); raise RuntimeError(str(e))

    def annuler_vente(self, vid: str) -> None:
        """Marque une vente comme annulee."""
        try:
            self.connexion.execute("UPDATE ventes SET annulee=1 WHERE id=?", (vid,))
            self.connexion.commit()
        except sqlite3.Error as e: self.connexion.rollback(); raise RuntimeError(str(e))

    def lister_ventes(self) -> list[Vente]:
        cur = self.connexion.execute(
            "SELECT id,client_nom,montant_total,lignes_json,structure_hospitaliere,date_vente,date_creation,produit_id,produit_nom,quantite,prix_unitaire,annulee FROM ventes ORDER BY date_vente DESC")
        result = []
        for r in cur.fetchall():
            result.append(Vente.from_dict({"id":r[0],"client_nom":r[1],"montant_total":r[2],
                "lignes_json":r[3],"structure_hospitaliere":r[4],"date_vente":r[5],"date_creation":r[6],
                "produit_id":r[7] or "","produit_nom":r[8] or "","quantite":r[9] or 0,"prix_unitaire":r[10] or 0,
                "annulee":r[11] if len(r)>11 else 0}))
        return result

    def obtenir_vente(self, vid: str) -> Optional[Vente]:
        cur = self.connexion.execute(
            "SELECT id,client_nom,montant_total,lignes_json,structure_hospitaliere,date_vente,date_creation,produit_id,produit_nom,quantite,prix_unitaire,annulee FROM ventes WHERE id=?", (vid,))
        r = cur.fetchone()
        if not r: return None
        return Vente.from_dict({"id":r[0],"client_nom":r[1],"montant_total":r[2],
            "lignes_json":r[3],"structure_hospitaliere":r[4],"date_vente":r[5],"date_creation":r[6],
            "produit_id":r[7] or "","produit_nom":r[8] or "","quantite":r[9] or 0,"prix_unitaire":r[10] or 0,
            "annulee":r[11] if len(r)>11 else 0})

    # ═══════════ ARRIVAGES ═══════════
    def ajouter_arrivage(self, a: Arrivage) -> None:
        d = a.to_dict()
        try:
            self.connexion.execute(
                "INSERT INTO arrivages(id,produit_id,quantite,quantite_restante,fournisseur,description,date_peremption,date_arrivage,date_creation) VALUES(?,?,?,?,?,?,?,?,?)",
                (d["id"],d["produit_id"],d["quantite"],d["quantite_restante"],d["fournisseur"],d["description"],d["date_peremption"],d["date_arrivage"],d["date_creation"]))
            self.connexion.commit()
        except sqlite3.Error as e: self.connexion.rollback(); raise RuntimeError(str(e))

    def lister_arrivages(self, produit_id: str = "") -> list[Arrivage]:
        if produit_id:
            cur = self.connexion.execute("SELECT id,produit_id,quantite,fournisseur,description,date_peremption,date_arrivage,date_creation,quantite_restante FROM arrivages WHERE produit_id=? ORDER BY date_arrivage DESC", (produit_id,))
        else:
            cur = self.connexion.execute("SELECT id,produit_id,quantite,fournisseur,description,date_peremption,date_arrivage,date_creation,quantite_restante FROM arrivages ORDER BY date_arrivage DESC")
        result = []
        for r in cur.fetchall():
            qr = r[8] if len(r)>8 else r[2]
            result.append(Arrivage.from_dict({"id":r[0],"produit_id":r[1],"quantite":r[2],"fournisseur":r[3],"description":r[4],"date_peremption":r[5],"date_arrivage":r[6],"date_creation":r[7],"quantite_restante":qr}))
        return result

    def lister_lots_vendables(self, produit_id: str) -> list[Arrivage]:
        """Lots avec stock > 0 et non périmés, triés par date péremption (FEFO)."""
        today = date.today().isoformat()
        cur = self.connexion.execute(
            """SELECT id,produit_id,quantite,fournisseur,description,date_peremption,date_arrivage,date_creation,quantite_restante
               FROM arrivages WHERE produit_id=? AND quantite_restante>0
               AND (date_peremption>=? OR date_peremption='')
               ORDER BY CASE WHEN date_peremption='' THEN '9999-12-31' ELSE date_peremption END ASC""",
            (produit_id, today))
        result = []
        for r in cur.fetchall():
            qr = r[8] if len(r)>8 else r[2]
            result.append(Arrivage.from_dict({"id":r[0],"produit_id":r[1],"quantite":r[2],"fournisseur":r[3],"description":r[4],"date_peremption":r[5],"date_arrivage":r[6],"date_creation":r[7],"quantite_restante":qr}))
        return result

    def modifier_arrivage_qte_restante(self, arrivage_id: str, nouvelle_qte: int) -> None:
        try:
            self.connexion.execute("UPDATE arrivages SET quantite_restante=? WHERE id=?", (max(0,nouvelle_qte), arrivage_id))
            self.connexion.commit()
        except sqlite3.Error as e: self.connexion.rollback(); raise RuntimeError(str(e))

    # ═══════════ MOUVEMENTS STOCK ═══════════
    def ajouter_mouvement(self, m: MouvementStock) -> None:
        d = m.to_dict()
        try:
            self.connexion.execute(
                "INSERT INTO mouvements_stock VALUES(?,?,?,?,?,?,?,?)",
                (d["id"],d["produit_id"],d["produit_nom"],d["type_mvt"],d["quantite"],d["description"],d["date_mvt"],d["date_creation"]))
            self.connexion.commit()
        except sqlite3.Error as e: self.connexion.rollback(); raise RuntimeError(str(e))

    def lister_mouvements(self, produit_id: str = "") -> list[MouvementStock]:
        if produit_id:
            cur = self.connexion.execute("SELECT id,produit_id,produit_nom,type_mvt,quantite,description,date_mvt,date_creation FROM mouvements_stock WHERE produit_id=? ORDER BY date_mvt DESC", (produit_id,))
        else:
            cur = self.connexion.execute("SELECT id,produit_id,produit_nom,type_mvt,quantite,description,date_mvt,date_creation FROM mouvements_stock ORDER BY date_mvt DESC")
        return [MouvementStock.from_dict({"id":r[0],"produit_id":r[1],"produit_nom":r[2],"type_mvt":r[3],"quantite":r[4],"description":r[5],"date_mvt":r[6],"date_creation":r[7]}) for r in cur.fetchall()]

    # ═══════════ HISTORIQUE ACTIONS ═══════════
    def ajouter_action(self, h: HistoriqueAction) -> None:
        d = h.to_dict()
        try:
            self.connexion.execute(
                "INSERT INTO historique_actions VALUES(?,?,?,?,?,?,?)",
                (d["id"],d["utilisateur"],d["action"],d["description"],d["cible"],d["date_action"],d["date_creation"]))
            self.connexion.commit()
        except sqlite3.Error as e: self.connexion.rollback(); raise RuntimeError(str(e))

    def lister_actions(self, limit: int = 100) -> list[HistoriqueAction]:
        cur = self.connexion.execute("SELECT id,utilisateur,action,description,cible,date_action,date_creation FROM historique_actions ORDER BY date_action DESC LIMIT ?", (limit,))
        return [HistoriqueAction.from_dict({"id":r[0],"utilisateur":r[1],"action":r[2],"description":r[3],"cible":r[4],"date_action":r[5],"date_creation":r[6]}) for r in cur.fetchall()]

    def filtrer_actions(self, terme:str="", action_type:str="") -> list[HistoriqueAction]:
        sql = "SELECT id,utilisateur,action,description,cible,date_action,date_creation FROM historique_actions WHERE 1=1"
        params = []
        if terme:
            sql += " AND (description LIKE ? OR utilisateur LIKE ? OR cible LIKE ?)"
            params += [f"%{terme}%"]*3
        if action_type:
            sql += " AND action LIKE ?"; params.append(f"%{action_type}%")
        sql += " ORDER BY date_action DESC LIMIT 500"
        cur = self.connexion.execute(sql, params)
        return [HistoriqueAction.from_dict({"id":r[0],"utilisateur":r[1],"action":r[2],"description":r[3],"cible":r[4],"date_action":r[5],"date_creation":r[6]}) for r in cur.fetchall()]

    # ═══════════ UTILISATEURS ═══════════
    def ajouter_utilisateur(self, u: Utilisateur) -> None:
        cur = self.connexion.execute("SELECT COUNT(*) FROM utilisateurs")
        if cur.fetchone()[0] == 0:
            u.is_admin = True
        d = u.to_dict()
        try:
            self.connexion.execute(
                """INSERT INTO utilisateurs(id,username,email,password_hash,is_admin,
                   security_question,security_answer_hash,must_change_password,date_creation)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (d["id"],d["username"],d["email"],d["password_hash"],d["is_admin"],
                 d.get("security_question",""),d.get("security_answer_hash",""),
                 d.get("must_change_password",0),d["date_creation"]))
            self.connexion.commit()
        except sqlite3.IntegrityError as e: self.connexion.rollback(); raise ValueError(str(e))
        except sqlite3.Error as e: self.connexion.rollback(); raise RuntimeError(str(e))

    def obtenir_utilisateur_par_nom(self, username: str) -> Optional[Utilisateur]:
        cur = self.connexion.execute("SELECT * FROM utilisateurs WHERE username=?", (username,))
        r = cur.fetchone()
        if not r: return None
        cols = [desc[0] for desc in cur.description]
        dd = dict(zip(cols,r))
        dd.setdefault("security_question",""); dd.setdefault("security_answer_hash",""); dd.setdefault("must_change_password",0)
        return Utilisateur.from_dict(dd)

    def obtenir_utilisateur_par_email(self, email: str) -> Optional[Utilisateur]:
        cur = self.connexion.execute("SELECT * FROM utilisateurs WHERE email=?", (email,))
        r = cur.fetchone()
        if not r: return None
        cols = [desc[0] for desc in cur.description]
        dd = dict(zip(cols,r))
        dd.setdefault("security_question",""); dd.setdefault("security_answer_hash",""); dd.setdefault("must_change_password",0)
        return Utilisateur.from_dict(dd)

    def supprimer_utilisateur(self, uid: str) -> None:
        """Supprime un compte utilisateur."""
        self.connexion.execute("DELETE FROM utilisateurs WHERE id=?", (uid,))
        self.connexion.commit()

    def reinitialiser_base(self) -> None:
        """Supprime toutes les données pour repartir de zéro."""
        for t in ["ventes","mouvements","arrivages","produits","categories","utilisateurs","historique_actions"]:
            try: self.connexion.execute(f"DELETE FROM {t}")
            except: pass
        self.connexion.commit()
        # Réinsérer les catégories par défaut
        for nom in ["Antibiotiques","Antalgiques","Anti-inflammatoires","Vitamines & Compléments",
                     "Dermatologie","Pédiatrie","Ophtalmologie","Divers"]:
            c = Categorie(nom=nom)
            self.connexion.execute("INSERT INTO categories VALUES(?,?,?)", (c.id, nom, c.date_creation))
        self.connexion.commit()

    def modifier_utilisateur(self, u) -> None:
        """Met à jour un utilisateur (mot de passe, question sécurité, etc.)."""
        self.connexion.execute(
            """UPDATE utilisateurs SET password_hash=?, security_question=?,
               security_answer_hash=?, must_change_password=? WHERE id=?""",
            (u.password_hash, u.security_question, u.security_answer_hash,
             int(u.must_change_password), u.id))
        self.connexion.commit()

    def lister_utilisateurs(self) -> list[Utilisateur]:
        """Liste tous les utilisateurs (pour admin)."""
        cur = self.connexion.execute("SELECT * FROM utilisateurs ORDER BY username")
        cols = [desc[0] for desc in cur.description]
        result = []
        for r in cur.fetchall():
            dd = dict(zip(cols,r))
            dd.setdefault("security_question",""); dd.setdefault("security_answer_hash",""); dd.setdefault("must_change_password",0)
            result.append(Utilisateur.from_dict(dd))
        return result

    # ═══════════ STATISTIQUES ═══════════
    def statistiques_jour(self) -> dict:
        """Statistiques du jour uniquement (réinitialisées à 5h00)."""
        from datetime import datetime as dt_cls
        now = dt_cls.now()
        if now.hour < 5:
            jour_debut = (now - timedelta(days=1)).strftime("%Y-%m-%dT05:00:00")
        else:
            jour_debut = now.strftime("%Y-%m-%dT05:00:00")
        jour_fin = (dt_cls.fromisoformat(jour_debut) + timedelta(days=1)).isoformat()
        c = self.connexion.cursor()
        c.execute("SELECT COUNT(*) FROM ventes WHERE annulee=0 AND date_vente>=? AND date_vente<?", (jour_debut, jour_fin))
        nb_v = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(montant_total),0) FROM ventes WHERE annulee=0 AND date_vente>=? AND date_vente<?", (jour_debut, jour_fin))
        ca = c.fetchone()[0]
        return {"nb_ventes_jour": nb_v, "ca_jour": ca}

    def statistiques(self) -> dict:
        try:
            c = self.connexion.cursor()
            c.execute("SELECT COUNT(*) FROM produits"); nb_p=c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM produits WHERE quantite=0"); nb_r=c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM produits WHERE quantite>0 AND quantite<=10"); nb_b=c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM ventes WHERE annulee=0"); nb_v=c.fetchone()[0]
            c.execute("SELECT COALESCE(SUM(montant_total),0) FROM ventes WHERE annulee=0"); ca=c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM categories"); nb_c=c.fetchone()[0]
            # Alertes peremption par lot
            seuil = (date.today()+timedelta(days=30)).isoformat()
            c.execute("SELECT COUNT(*) FROM arrivages WHERE date_peremption<=? AND date_peremption!='' AND quantite_restante>0", (seuil,))
            nb_exp=c.fetchone()[0]
            # Lots perimes non vides
            nb_perimes = len(self.lots_perimes_non_vides())
            ventes_mois = []
            for i in range(11,-1,-1):
                d1 = date.today().replace(day=1)
                for _ in range(i):
                    d1 = (d1 - timedelta(days=1)).replace(day=1)
                if d1.month == 12: d2 = d1.replace(year=d1.year+1, month=1)
                else: d2 = d1.replace(month=d1.month+1)
                c.execute("SELECT COALESCE(SUM(montant_total),0) FROM ventes WHERE annulee=0 AND date_vente>=? AND date_vente<?",
                           (d1.isoformat(), d2.isoformat()))
                ventes_mois.append({"mois":d1.strftime("%b %Y"),"total":c.fetchone()[0]})
            return {"nb_produits":nb_p,"nb_rupture":nb_r,"nb_stock_bas":nb_b,"nb_ventes":nb_v,
                    "chiffre_affaires":ca,"nb_categories":nb_c,"nb_expiration_proche":nb_exp,
                    "nb_lots_perimes":nb_perimes,"ventes_mois":ventes_mois}
        except: return {k:0 for k in ("nb_produits","nb_rupture","nb_stock_bas","nb_ventes","chiffre_affaires","nb_categories","nb_expiration_proche","nb_lots_perimes")}

    def ca_par_periode(self, date_debut: str, date_fin: str) -> float:
        """CA entre deux dates (non annulees)."""
        cur = self.connexion.execute(
            "SELECT COALESCE(SUM(montant_total),0) FROM ventes WHERE annulee=0 AND date_vente>=? AND date_vente<?",
            (date_debut, date_fin))
        return cur.fetchone()[0]

    def ca_journalier(self, jour: str) -> float:
        """CA d'un jour (reinitialise a 5h: de jour 05:00 a jour+1 05:00)."""
        try:
            d = date.fromisoformat(jour)
            debut = datetime(d.year, d.month, d.day, 5, 0, 0).isoformat()
            fin = datetime(d.year, d.month, d.day + 1 if d.day < 28 else 1, 5, 0, 0)
            # Calcul propre du lendemain
            lendemain = d + timedelta(days=1)
            fin = datetime(lendemain.year, lendemain.month, lendemain.day, 5, 0, 0).isoformat()
            return self.ca_par_periode(debut, fin)
        except: return 0.0

    def ventes_par_jour(self, date_debut: str, date_fin: str) -> list[dict]:
        """Retourne CA par jour sur une plage."""
        result = []
        try:
            d = date.fromisoformat(date_debut)
            fin = date.fromisoformat(date_fin)
            while d <= fin:
                ca = self.ca_journalier(d.isoformat())
                result.append({"jour": d.isoformat(), "ca": ca})
                d += timedelta(days=1)
        except: pass
        return result

    def ventes_par_semaine(self, date_debut: str, date_fin: str) -> list[dict]:
        """Retourne le CA par semaine sur une plage."""
        result = []
        try:
            d = date.fromisoformat(date_debut)
            d = d - timedelta(days=d.weekday())  # lundi
            fin = date.fromisoformat(date_fin)
            while d <= fin:
                d2 = d + timedelta(days=7)
                ca = self.ca_par_periode(d.isoformat(), d2.isoformat())
                sem = d.isocalendar()[1]
                result.append({"semaine": f"S{sem} ({d.strftime('%d/%m')})", "ca": ca})
                d = d2
        except: pass
        return result

    def ventes_par_mois(self, date_debut: str, date_fin: str) -> list[dict]:
        """Retourne CA par mois sur une plage."""
        result = []
        try:
            d = date.fromisoformat(date_debut).replace(day=1)
            fin = date.fromisoformat(date_fin)
            while d <= fin:
                if d.month == 12: d2 = d.replace(year=d.year+1, month=1)
                else: d2 = d.replace(month=d.month+1)
                ca = self.ca_par_periode(d.isoformat(), d2.isoformat())
                result.append({"mois": d.strftime("%b %Y"), "ca": ca})
                d = d2
        except: pass
        return result

    def ventes_par_produit(self, date_debut: str, date_fin: str) -> list[dict]:
        """Retourne quantités et CA par produit sur une plage (hors annulées)."""
        ventes = self.lister_ventes()
        from collections import defaultdict
        agg = defaultdict(lambda: {"quantite_totale": 0, "ca": 0})
        for v in ventes:
            if v.annulee: continue
            dv = v.date_vente[:10]
            if dv < date_debut or dv > date_fin: continue
            for l in v.lignes:
                pn = l.get("produit_nom", "Inconnu")
                agg[pn]["quantite_totale"] += l.get("quantite", 0)
                agg[pn]["ca"] += l.get("sous_total", 0)
        result = [{"produit_nom": k, **v} for k, v in agg.items()]
        result.sort(key=lambda x: x["ca"], reverse=True)
        return result

    def ventes_par_categorie(self, date_debut: str, date_fin: str) -> list[dict]:
        """Retourne quantités et CA agrégés par catégorie sur une plage (hors annulées)."""
        ventes = self.lister_ventes()
        cats = {c.id: c.nom for c in self.lister_categories()}
        prods = {p.id: p for p in self.lister_produits()}
        from collections import defaultdict
        agg = defaultdict(lambda: {"quantite_totale": 0, "ca": 0})
        for v in ventes:
            if v.annulee: continue
            dv = v.date_vente[:10]
            if dv < date_debut or dv > date_fin: continue
            for l in v.lignes:
                pid = l.get("produit_id", "")
                p = prods.get(pid)
                cat_nom = cats.get(p.categorie_id, "Autre") if p else "Autre"
                agg[cat_nom]["quantite_totale"] += l.get("quantite", 0)
                agg[cat_nom]["ca"] += l.get("sous_total", 0)
        result = [{"categorie_nom": k, **v} for k, v in agg.items()]
        result.sort(key=lambda x: x["ca"], reverse=True)
        return result

    # ═══════════ EXPORTS ═══════════
    def exporter_csv(self, filepath: str) -> None:
        prods = self.lister_produits()
        cats = {c.id:c.nom for c in self.lister_categories()}
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Nom","Catégorie","Prix","Quantité","Sur ordonnance","Description"])
            for p in prods:
                w.writerow([p.nom,cats.get(p.categorie_id,""),p.prix,p.quantite,
                            "Oui" if p.sur_ordonnance else "Non",p.description])

    def exporter_ventes_csv(self, filepath: str) -> None:
        ventes = self.lister_ventes()
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["ID","Client","Structure","Montant","Date","Annulee","Details"])
            for v in ventes:
                details = "; ".join([f"{l.get('produit_nom','')} x{l.get('quantite','')}" for l in v.lignes]) if v.lignes else v.produit_nom
                w.writerow([v.id[:12],v.client_nom,v.structure_hospitaliere,v.montant_total,v.date_vente[:19],"Oui" if v.annulee else "Non",details])

    def sauvegarder_base(self, dest: str) -> str:
        self.connexion.commit()
        backup = os.path.join(dest, f"pharmacie_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        shutil.copy2(self.__db_path, backup)
        return backup
