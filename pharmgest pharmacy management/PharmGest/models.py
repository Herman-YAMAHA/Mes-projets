"""
models.py v4 — Logique metier PharmGest.
v4: Stock par lot (quantite_restante dans Arrivage), annulation facture (3h),
    validation email, notification peremption, vente par lot.
"""
from __future__ import annotations
import uuid, hashlib, re, json
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional

class StatutStock(Enum):
    RUPTURE="red"; BAS="orange"; NORMAL="green"
class TypeMouvement(Enum):
    ENTREE="Entree"; VENTE="Vente"; CI="Consommation interne"; PERTE="Perte"; ANNULATION="Annulation"

class EntiteBase(ABC):
    def __init__(self, id_entite: Optional[str]=None) -> None:
        self.__id: str = id_entite or uuid.uuid4().hex[:12]
        self.__date_creation: str = datetime.now().isoformat()
    @property
    def id(self) -> str: return self.__id
    @property
    def date_creation(self) -> str: return self.__date_creation
    @date_creation.setter
    def date_creation(self, v: str) -> None: self.__date_creation = v
    @abstractmethod
    def resume(self) -> str: ...
    @abstractmethod
    def to_dict(self) -> dict: ...

class Categorie(EntiteBase):
    def __init__(self, nom: str, id_entite: Optional[str]=None) -> None:
        super().__init__(id_entite); self.__nom = nom
    @property
    def nom(self) -> str: return self.__nom
    @nom.setter
    def nom(self, v: str) -> None:
        if not v or not v.strip(): raise ValueError("Nom catégorie vide.")
        self.__nom = v.strip()
    def resume(self) -> str: return f"Catégorie : {self.__nom}"
    def to_dict(self) -> dict: return {"id":self.id,"nom":self.__nom,"date_creation":self.date_creation}
    @classmethod
    def from_dict(cls, d: dict) -> Categorie:
        o=cls(nom=d["nom"],id_entite=d["id"]); o.date_creation=d.get("date_creation",""); return o
    def __str__(self) -> str: return self.__nom

class Produit(EntiteBase):
    """Produit: quantite globale = somme des quantite_restante des arrivages non expires."""
    def __init__(self, nom:str, categorie_id:str, prix:float,
                 quantite:int=0, description:str="", date_expiration:str="",
                 sur_ordonnance:bool=False, id_entite:Optional[str]=None) -> None:
        super().__init__(id_entite)
        self.__nom=nom; self.__categorie_id=categorie_id; self.__prix=prix
        self.__quantite=quantite; self.__description=description
        self.__date_expiration=date_expiration; self.__sur_ordonnance=sur_ordonnance
    @property
    def nom(self)->str: return self.__nom
    @nom.setter
    def nom(self,v:str)->None:
        if not v or not v.strip(): raise ValueError("Nom produit obligatoire.")
        self.__nom=v.strip()
    @property
    def categorie_id(self)->str: return self.__categorie_id
    @categorie_id.setter
    def categorie_id(self,v:str)->None: self.__categorie_id=v
    @property
    def prix(self)->float: return self.__prix
    @prix.setter
    def prix(self,v:float)->None:
        if v<0: raise ValueError("Prix negatif interdit.")
        self.__prix=v
    @property
    def quantite(self)->int: return self.__quantite
    @quantite.setter
    def quantite(self,v:int)->None:
        if v<0: raise ValueError("Quantité négative interdite.")
        self.__quantite=v
    @property
    def description(self)->str: return self.__description
    @description.setter
    def description(self,v:str)->None: self.__description=v
    @property
    def date_expiration(self)->str: return self.__date_expiration
    @date_expiration.setter
    def date_expiration(self,v:str)->None: self.__date_expiration=v
    @property
    def sur_ordonnance(self)->bool: return self.__sur_ordonnance
    @sur_ordonnance.setter
    def sur_ordonnance(self,v:bool)->None: self.__sur_ordonnance=v
    def statut_stock(self)->StatutStock:
        if self.__quantite==0: return StatutStock.RUPTURE
        if self.__quantite<=10: return StatutStock.BAS
        return StatutStock.NORMAL
    def est_expire(self)->bool:
        try: return date.fromisoformat(self.__date_expiration)<date.today()
        except: return False
    def jours_avant_expiration(self)->int:
        try: return (date.fromisoformat(self.__date_expiration)-date.today()).days
        except: return 9999
    def peut_etre_vendu(self)->tuple[bool,str]:
        if self.__quantite==0: return False,"Stock epuise."
        return True,""
    def decrementer_stock(self,qte:int)->None:
        if qte>self.__quantite: raise ValueError(f"Stock insuffisant ({self.__quantite} dispo).")
        self.__quantite-=qte
    def incrementer_stock(self,qte:int)->None:
        if qte<=0: raise ValueError("Quantité > 0 requise.")
        self.__quantite+=qte
    @staticmethod
    def valider_date_expiration(d:str)->tuple[bool,str]:
        try:
            dt=date.fromisoformat(d)
            if dt<=date.today(): return False,"La date d'expiration doit etre future."
            return True,""
        except ValueError: return False,"Format de date invalide (AAAA-MM-JJ)."
    def resume(self)->str:
        s=self.statut_stock(); ordo=" [ORDONNANCE]" if self.__sur_ordonnance else ""
        return f"{self.__nom}{ordo} - {self.__prix:,.0f} FCFA | Stock:{self.__quantite} [{s.name}]"
    def to_dict(self)->dict:
        return {"id":self.id,"nom":self.__nom,"categorie_id":self.__categorie_id,
                "prix":self.__prix,"quantite":self.__quantite,"description":self.__description,
                "date_expiration":self.__date_expiration,"sur_ordonnance":int(self.__sur_ordonnance),
                "date_creation":self.date_creation}
    @classmethod
    def from_dict(cls,d:dict)->Produit:
        o=cls(nom=d["nom"],categorie_id=d["categorie_id"],prix=float(d["prix"]),
              quantite=int(d["quantite"]),description=d.get("description",""),
              date_expiration=d.get("date_expiration",""),
              sur_ordonnance=bool(int(d.get("sur_ordonnance",0))),id_entite=d["id"])
        o.date_creation=d.get("date_creation",""); return o

class Client(EntiteBase):
    def __init__(self,nom:str,id_entite:Optional[str]=None)->None:
        super().__init__(id_entite); self.__nom=nom
    @property
    def nom(self)->str: return self.__nom
    @nom.setter
    def nom(self,v:str)->None:
        if not v or not v.strip(): raise ValueError("Nom client obligatoire.")
        self.__nom=v.strip()
    def resume(self)->str: return f"Client : {self.__nom}"
    def to_dict(self)->dict: return {"id":self.id,"nom":self.__nom,"date_creation":self.date_creation}
    @classmethod
    def from_dict(cls,d:dict)->Client:
        o=cls(nom=d["nom"],id_entite=d["id"]); o.date_creation=d.get("date_creation",""); return o

class LigneFacture:
    def __init__(self,produit_id:str,produit_nom:str,prix_unitaire:float,quantite:int,
                 arrivage_id:str="")->None:
        self.__produit_id=produit_id; self.__produit_nom=produit_nom
        self.__prix_unitaire=prix_unitaire; self.__quantite=quantite
        self.__sous_total=prix_unitaire*quantite
        self.__arrivage_id=arrivage_id
    @property
    def produit_id(self)->str: return self.__produit_id
    @property
    def produit_nom(self)->str: return self.__produit_nom
    @property
    def prix_unitaire(self)->float: return self.__prix_unitaire
    @property
    def quantite(self)->int: return self.__quantite
    @property
    def sous_total(self)->float: return self.__sous_total
    @property
    def arrivage_id(self)->str: return self.__arrivage_id
    def to_dict(self)->dict:
        return {"produit_id":self.__produit_id,"produit_nom":self.__produit_nom,
                "prix_unitaire":self.__prix_unitaire,"quantite":self.__quantite,
                "sous_total":self.__sous_total,"arrivage_id":self.__arrivage_id}

class Vente(EntiteBase):
    def __init__(self,client_nom:str="",montant_total:float=0,lignes:list=None,
                 structure_hospitaliere:str="",date_vente:Optional[str]=None,
                 id_entite:Optional[str]=None,produit_id:str="",produit_nom:str="",
                 quantite:int=0,prix_unitaire:float=0,annulee:bool=False)->None:
        super().__init__(id_entite)
        self.__client_nom=client_nom; self.__montant_total=montant_total
        self.__lignes=lignes or []; self.__structure_hospitaliere=structure_hospitaliere
        self.__date_vente=date_vente or datetime.now().isoformat()
        self.__produit_id=produit_id; self.__produit_nom=produit_nom
        self.__quantite=quantite; self.__prix_unitaire=prix_unitaire
        self.__annulee=annulee
    @property
    def client_nom(self)->str: return self.__client_nom
    @property
    def montant_total(self)->float: return self.__montant_total
    @property
    def lignes(self)->list: return self.__lignes
    @property
    def structure_hospitaliere(self)->str: return self.__structure_hospitaliere
    @property
    def date_vente(self)->str: return self.__date_vente
    @property
    def produit_id(self)->str: return self.__produit_id
    @property
    def produit_nom(self)->str: return self.__produit_nom
    @property
    def quantite(self)->int: return self.__quantite
    @property
    def prix_unitaire(self)->float: return self.__prix_unitaire
    @property
    def annulee(self)->bool: return self.__annulee
    @annulee.setter
    def annulee(self,v:bool)->None: self.__annulee=v
    def peut_etre_annulee(self)->tuple[bool,str]:
        """Annulation possible dans les 3h suivant la vente."""
        if self.__annulee: return False,"Cette facture est déjà annulée."
        try:
            dt=datetime.fromisoformat(self.__date_vente)
            if datetime.now()-dt>timedelta(hours=3):
                return False,"Delai d'annulation depasse (3h max)."
        except: pass
        return True,""
    def resume(self)->str:
        n=len(self.__lignes); ann=" [ANNULEE]" if self.__annulee else ""
        return f"Facture #{self.id[:8]}{ann} - {n} article(s) -> {self.__montant_total:,.0f} FCFA ({self.__client_nom})"
    def to_dict(self)->dict:
        return {"id":self.id,"client_nom":self.__client_nom,"montant_total":self.__montant_total,
                "lignes_json":json.dumps(self.__lignes,ensure_ascii=False),
                "structure_hospitaliere":self.__structure_hospitaliere,
                "date_vente":self.__date_vente,"date_creation":self.date_creation,
                "produit_id":self.__produit_id,"produit_nom":self.__produit_nom,
                "quantite":self.__quantite,"prix_unitaire":self.__prix_unitaire,
                "annulee":int(self.__annulee)}
    @classmethod
    def from_dict(cls,d:dict)->Vente:
        raw=d.get("lignes_json","[]")
        try: lignes=json.loads(raw) if raw else []
        except: lignes=[]
        o=cls(client_nom=d.get("client_nom",""),montant_total=float(d.get("montant_total",0)),
              lignes=lignes,structure_hospitaliere=d.get("structure_hospitaliere",""),
              date_vente=d.get("date_vente"),id_entite=d["id"],
              produit_id=d.get("produit_id",""),produit_nom=d.get("produit_nom",""),
              quantite=int(d.get("quantite",0)),prix_unitaire=float(d.get("prix_unitaire",0)),
              annulee=bool(int(d.get("annulee",0))))
        o.date_creation=d.get("date_creation",""); return o

class Arrivage(EntiteBase):
    """Arrivage v4: quantite_restante par lot pour gestion stock par lot."""
    def __init__(self,produit_id:str,quantite:int,fournisseur:str="",
                 description:str="",date_peremption:str="",
                 quantite_restante:Optional[int]=None,
                 date_arrivage:Optional[str]=None,
                 id_entite:Optional[str]=None)->None:
        super().__init__(id_entite)
        self.__produit_id=produit_id; self.__quantite=quantite
        self.__quantite_restante=quantite_restante if quantite_restante is not None else quantite
        self.__fournisseur=fournisseur; self.__description=description
        self.__date_peremption=date_peremption
        self.__date_arrivage=date_arrivage or datetime.now().isoformat()
    @property
    def produit_id(self)->str: return self.__produit_id
    @property
    def quantite(self)->int: return self.__quantite
    @property
    def quantite_restante(self)->int: return self.__quantite_restante
    @quantite_restante.setter
    def quantite_restante(self,v:int)->None: self.__quantite_restante=max(0,v)
    @property
    def fournisseur(self)->str: return self.__fournisseur
    @property
    def description(self)->str: return self.__description
    @property
    def date_peremption(self)->str: return self.__date_peremption
    @property
    def date_arrivage(self)->str: return self.__date_arrivage
    def est_perime(self)->bool:
        if not self.__date_peremption: return False
        try: return date.fromisoformat(self.__date_peremption)<date.today()
        except: return False
    def jours_avant_peremption(self)->int:
        if not self.__date_peremption: return 9999
        try: return (date.fromisoformat(self.__date_peremption)-date.today()).days
        except: return 9999
    def resume(self)->str: return f"Arrivage +{self.__quantite} rest:{self.__quantite_restante} ({self.__fournisseur}) exp:{self.__date_peremption}"
    def to_dict(self)->dict:
        return {"id":self.id,"produit_id":self.__produit_id,"quantite":self.__quantite,
                "quantite_restante":self.__quantite_restante,
                "fournisseur":self.__fournisseur,"description":self.__description,
                "date_peremption":self.__date_peremption,
                "date_arrivage":self.__date_arrivage,"date_creation":self.date_creation}
    @classmethod
    def from_dict(cls,d:dict)->Arrivage:
        o=cls(produit_id=d["produit_id"],quantite=int(d["quantite"]),
              quantite_restante=int(d["quantite_restante"]) if "quantite_restante" in d and d["quantite_restante"] is not None else int(d["quantite"]),
              fournisseur=d.get("fournisseur",""),description=d.get("description",""),
              date_peremption=d.get("date_peremption",""),
              date_arrivage=d.get("date_arrivage"),id_entite=d["id"])
        o.date_creation=d.get("date_creation",""); return o

class MouvementStock(EntiteBase):
    """v3: description obligatoire pour tout mouvement."""
    def __init__(self,produit_id:str,produit_nom:str,type_mvt:str,quantite:int,
                 description:str="",date_mvt:Optional[str]=None,
                 id_entite:Optional[str]=None)->None:
        super().__init__(id_entite)
        if not description.strip(): raise ValueError("Description obligatoire pour tout mouvement de stock.")
        self.__produit_id=produit_id; self.__produit_nom=produit_nom
        self.__type_mvt=type_mvt; self.__quantite=quantite
        self.__description=description; self.__date_mvt=date_mvt or datetime.now().isoformat()
    @property
    def produit_id(self)->str: return self.__produit_id
    @property
    def produit_nom(self)->str: return self.__produit_nom
    @property
    def type_mvt(self)->str: return self.__type_mvt
    @property
    def quantite(self)->int: return self.__quantite
    @property
    def description(self)->str: return self.__description
    @property
    def date_mvt(self)->str: return self.__date_mvt
    def resume(self)->str: return f"[{self.__type_mvt}] {self.__produit_nom} x{self.__quantite}"
    def to_dict(self)->dict:
        return {"id":self.id,"produit_id":self.__produit_id,"produit_nom":self.__produit_nom,
                "type_mvt":self.__type_mvt,"quantite":self.__quantite,
                "description":self.__description,"date_mvt":self.__date_mvt,
                "date_creation":self.date_creation}
    @classmethod
    def from_dict(cls,d:dict)->MouvementStock:
        o=cls(produit_id=d["produit_id"],produit_nom=d.get("produit_nom",""),
              type_mvt=d["type_mvt"],quantite=int(d["quantite"]),
              description=d.get("description","") or "Import",date_mvt=d.get("date_mvt"),id_entite=d["id"])
        o.date_creation=d.get("date_creation",""); return o

class HistoriqueAction(EntiteBase):
    def __init__(self,utilisateur:str,action:str,description:str,cible:str="",
                 date_action:Optional[str]=None,id_entite:Optional[str]=None)->None:
        super().__init__(id_entite)
        if not description.strip(): raise ValueError("Description d'action obligatoire.")
        self.__utilisateur=utilisateur; self.__action=action
        self.__description=description; self.__cible=cible
        self.__date_action=date_action or datetime.now().isoformat()
    @property
    def utilisateur(self)->str: return self.__utilisateur
    @property
    def action(self)->str: return self.__action
    @property
    def description(self)->str: return self.__description
    @property
    def cible(self)->str: return self.__cible
    @property
    def date_action(self)->str: return self.__date_action
    def resume(self)->str: return f"[{self.__action}] {self.__description} - par {self.__utilisateur}"
    def to_dict(self)->dict:
        return {"id":self.id,"utilisateur":self.__utilisateur,"action":self.__action,
                "description":self.__description,"cible":self.__cible,
                "date_action":self.__date_action,"date_creation":self.date_creation}
    @classmethod
    def from_dict(cls,d:dict)->HistoriqueAction:
        o=cls(utilisateur=d["utilisateur"],action=d["action"],description=d["description"],
              cible=d.get("cible",""),date_action=d.get("date_action"),id_entite=d["id"])
        o.date_creation=d.get("date_creation",""); return o

class Utilisateur(EntiteBase):
    def __init__(self,username:str,email:str,password_hash:str,
                 is_admin:bool=False,security_question:str="",security_answer_hash:str="",
                 must_change_password:bool=False,id_entite:Optional[str]=None)->None:
        super().__init__(id_entite)
        self.__username=username; self.__email=email
        self.__password_hash=password_hash; self.__is_admin=is_admin
        self.__security_question=security_question
        self.__security_answer_hash=security_answer_hash
        self.__must_change_password=must_change_password
    @property
    def username(self)->str: return self.__username
    @property
    def email(self)->str: return self.__email
    @property
    def password_hash(self)->str: return self.__password_hash
    @password_hash.setter
    def password_hash(self,v:str)->None: self.__password_hash=v
    @property
    def is_admin(self)->bool: return self.__is_admin
    @property
    def security_question(self)->str: return self.__security_question
    @security_question.setter
    def security_question(self,v:str)->None: self.__security_question=v
    @property
    def security_answer_hash(self)->str: return self.__security_answer_hash
    @security_answer_hash.setter
    def security_answer_hash(self,v:str)->None: self.__security_answer_hash=v
    @property
    def must_change_password(self)->bool: return self.__must_change_password
    @must_change_password.setter
    def must_change_password(self,v:bool)->None: self.__must_change_password=v
    @is_admin.setter
    def is_admin(self,v:bool)->None: self.__is_admin=v
    def resume(self)->str:
        r="Admin" if self.__is_admin else "Utilisateur"
        return f"{r} : {self.__username} ({self.__email})"
    def to_dict(self)->dict:
        return {"id":self.id,"username":self.__username,"email":self.__email,
                "password_hash":self.__password_hash,"is_admin":int(self.__is_admin),
                "security_question":self.__security_question,
                "security_answer_hash":self.__security_answer_hash,
                "must_change_password":int(self.__must_change_password),
                "date_creation":self.date_creation}
    @classmethod
    def from_dict(cls,d:dict)->Utilisateur:
        o=cls(username=d["username"],email=d["email"],password_hash=d["password_hash"],
              is_admin=bool(int(d.get("is_admin",0))),
              security_question=d.get("security_question",""),
              security_answer_hash=d.get("security_answer_hash",""),
              must_change_password=bool(int(d.get("must_change_password",0))),
              id_entite=d["id"])
        o.date_creation=d.get("date_creation",""); return o
    @staticmethod
    def hasher_mot_de_passe(mdp:str)->str: return hashlib.sha256(mdp.encode()).hexdigest()
    def verifier_mot_de_passe(self,mdp:str)->bool:
        return self.__password_hash==self.hasher_mot_de_passe(mdp)
    def verifier_reponse_securite(self,reponse:str)->bool:
        return self.__security_answer_hash==self.hasher_mot_de_passe(reponse.strip().lower())
    @staticmethod
    def generer_mdp_temporaire()->str:
        import secrets, string
        chars=string.ascii_letters+string.digits+"!@#$%"
        return "".join(secrets.choice(chars) for _ in range(12))
    @staticmethod
    def valider_mot_de_passe(mdp:str)->tuple[bool,str]:
        if len(mdp)<8: return False,"Minimum 8 caractères."
        if not re.search(r"[A-Za-z]",mdp): return False,"Au moins une lettre."
        if not re.search(r"\d",mdp): return False,"Au moins un chiffre."
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]',mdp): return False,"Au moins un caractère spécial."
        return True,""
    @staticmethod
    def valider_email(email:str)->tuple[bool,str]:
        """Validation basique email: xxxx@xxxx.xxxx"""
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern,email):
            return False,"Format email invalide (attendu: xxxx@xxxx.xxxx)."
        return True,""
