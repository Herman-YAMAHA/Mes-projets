"""
gui.py v4 - Interface PharmGest.
v4: Vente par lot, annulation facture 3h, alertes péremption tous, catégories dans Admin,
    détail facture complet, validation e-mail, utilisateurs admin, CA personnalisable,
    notification lots périmés, suppression lots vides.
"""
from __future__ import annotations
import re, os, json
from datetime import date, datetime, timedelta
from tkinter import messagebox, StringVar, filedialog, simpledialog
from typing import Optional
import customtkinter as ctk
from models import *
from database import SQLiteDatabase

def _make_pwd_entry(parent, width=330, height=40, placeholder="••••••••", **kw):
    """Champ mot de passe avec bouton œil pour afficher/masquer."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.grid_columnconfigure(0, weight=1)
    entry = ctk.CTkEntry(frame, width=width-36, height=height, show="*", placeholder_text=placeholder, **kw)
    entry.grid(row=0, column=0, sticky="ew")
    vis = [False]
    btn = ctk.CTkButton(frame, text="👁", width=32, height=height,
                         fg_color="transparent", hover_color="#E2E8F0",
                         text_color="#64748B", font=ctk.CTkFont(size=14), command=lambda: None)
    def _toggle():
        vis[0] = not vis[0]
        entry.configure(show="" if vis[0] else "*")
        btn.configure(text="🙈" if vis[0] else "👁")
    btn.configure(command=_toggle)
    btn.grid(row=0, column=1, padx=(2, 0))
    frame._entry = entry
    return frame, entry

ctk.set_appearance_mode("light"); ctk.set_default_color_theme("blue")
C = {"pri":"#2563EB","pri_h":"#1D4ED8","sec":"#10B981","sec_h":"#059669",
     "danger":"#EF4444","warn":"#F59E0B","bg":"#F8FAFC","card":"#FFFFFF",
     "txt":"#1E293B","txt2":"#64748B","border":"#E2E8F0","admin":"#7C3AED","admin_h":"#6D28D9"}

class PharmacieApp(ctk.CTk):
    def __init__(self, db: SQLiteDatabase) -> None:
        super().__init__()
        self._db=db; self._user=None; self._frame=None
        self.title("PharmGest"); self.geometry("1180x760"); self.minsize(1050,680)
        self.configure(fg_color=C["bg"]); self.grid_rowconfigure(0,weight=1); self.grid_columnconfigure(0,weight=1)
        self.show(LoginFrame)
    @property
    def db(self): return self._db
    @property
    def user(self): return self._user
    @user.setter
    def user(self,u): self._user=u
    def show(self,cls,**kw):
        if self._frame: self._frame.destroy()
        self._frame=cls(self,self._db,**kw); self._frame.grid(row=0,column=0,sticky="nsew")
    def go_login(self): self.show(LoginFrame)
    def go_register(self): self.show(RegisterFrame)
    def go_dash(self): self.show(DashboardFrame)
    def go_produits(self): self.show(ProduitsFrame)
    def go_categories(self): self.show(CategoriesFrame)
    def go_ajout(self): self.show(AjoutProduitFrame)
    def go_modif(self,pid): self.show(ModifProduitFrame,produit_id=pid)
    def go_vente_groupee(self): self.show(VenteGroupeeFrame)
    def go_histo(self): self.show(HistoVentesFrame)
    def go_facture(self,vid): self.show(FactureFrame,vente_id=vid)
    def go_detail(self,pid): self.show(DetailProduitFrame,produit_id=pid)
    def go_admin(self): self.show(AdminFrame)
    def go_admin_arrivage(self): self.show(AdminArrivageFrame)
    def go_admin_mouvements(self): self.show(AdminMouvementsFrame)
    def go_admin_historique(self): self.show(AdminHistoriqueFrame)
    def go_admin_exports(self): self.show(AdminExportsFrame)
    def go_admin_categories(self): self.show(CategoriesFrame)
    def go_admin_utilisateurs(self): self.show(AdminUtilisateursFrame)
    def go_admin_ca(self): self.show(AdminCAFrame)
    def go_peremption(self): self.show(PeremptionFrame)
    def go_change_pwd(self): self.show(ChangerMdpFrame)
    def logout(self):
        if self._user: self.log_action("Déconnexion",f"Déconnexion de {self._user.username}",self._user.id)
        self._user=None; self.go_login()
    def log_action(self,action,desc,cible=""):
        try:
            u=self._user.username if self._user else "systeme"
            self._db.ajouter_action(HistoriqueAction(utilisateur=u,action=action,description=desc,cible=cible))
        except: pass

class SidebarMixin:
    def _sidebar(self, parent, app, active=""):
        sb=ctk.CTkFrame(parent,fg_color=C["pri"],width=225,corner_radius=0)
        sb.grid(row=0,column=0,sticky="ns"); sb.grid_propagate(False); sb.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(sb,text="  ⚕️ PharmGest",font=ctk.CTkFont(size=18,weight="bold"),text_color="white").grid(row=0,column=0,pady=(18,3),padx=10,sticky="w")
        if app.user:
            role="Admin" if app.user.is_admin else "Utilisateur"
            ctk.CTkLabel(sb,text=f"  {app.user.username} ({role})",text_color="#BFDBFE",font=ctk.CTkFont(size=10)).grid(row=1,column=0,pady=(0,14),padx=10,sticky="w")
        items=[("📊  Tableau de bord","dash",app.go_dash),("💊  Produits","prod",app.go_produits),("🛒  Nouvelle vente","vgrp",app.go_vente_groupee),("📋  Historique ventes","histo",app.go_histo),("⚠️  Alertes péremption","perm",app.go_peremption)]
        for i,(txt,key,cmd) in enumerate(items):
            a=key==active
            ctk.CTkButton(sb,text=f"  {txt}",anchor="w",width=200,height=34,fg_color="#1D4ED8" if a else "transparent",hover_color="#1E40AF",text_color="white",font=ctk.CTkFont(size=11,weight="bold" if a else "normal"),command=cmd).grid(row=i+2,column=0,padx=12,pady=2)
        sr=len(items)+2
        if app.user and app.user.is_admin:
            ctk.CTkFrame(sb,fg_color="#3B82F6",height=1).grid(row=sr,column=0,sticky="ew",padx=12,pady=8)
            ctk.CTkButton(sb,text="⚙️  Administration",anchor="w",width=200,height=34,fg_color=C["admin"] if active.startswith("adm") else "transparent",hover_color=C["admin_h"],text_color="#E0E7FF",font=ctk.CTkFont(size=11,weight="bold"),command=app.go_admin).grid(row=sr+1,column=0,padx=12,pady=2); sr+=2
        sb.grid_rowconfigure(sr,weight=1)
        try:
            perimes=app.db.lots_perimes_non_vides()
            if perimes:
                nf=ctk.CTkFrame(sb,fg_color="#DC2626",corner_radius=6)
                nf.grid(row=sr+1,column=0,padx=12,pady=(4,4),sticky="ew")
                ctk.CTkLabel(nf,text=f"  {len(perimes)} lot(s) périmé(s) !",text_color="white",font=ctk.CTkFont(size=10,weight="bold")).grid(row=0,column=0,padx=6,pady=4,sticky="w")
                sr+=1
        except: pass
        ctk.CTkButton(sb,text="🔑  Changer mot de passe",anchor="w",width=200,height=30,fg_color="transparent",hover_color="#1E40AF",text_color="#93C5FD",font=ctk.CTkFont(size=10),command=app.go_change_pwd).grid(row=sr+1,column=0,padx=12,pady=(4,2))
        ctk.CTkButton(sb,text="🚪  Déconnexion",anchor="w",width=200,height=34,fg_color="transparent",hover_color="#DC2626",text_color="#FCA5A5",command=app.logout).grid(row=sr+2,column=0,padx=12,pady=(0,18))

class LoginFrame(ctk.CTkFrame):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_rowconfigure(0,weight=1); self.grid_columnconfigure(0,weight=1)
        box=ctk.CTkFrame(self,fg_color=C["card"],corner_radius=18,width=400,height=520); box.grid(row=0,column=0); box.grid_propagate(False); box.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(box,text="⚕️ PharmGest",font=ctk.CTkFont(size=28,weight="bold"),text_color=C["pri"]).grid(row=0,column=0,pady=(35,5))
        ctk.CTkLabel(box,text="Connectez-vous",text_color=C["txt2"]).grid(row=1,column=0,pady=(0,25))
        ctk.CTkLabel(box,text="Nom d'utilisateur",anchor="w",text_color=C["txt"]).grid(row=2,column=0,sticky="w",padx=35)
        self._eu=ctk.CTkEntry(box,width=330,height=40,placeholder_text="Identifiant"); self._eu.grid(row=3,column=0,padx=35,pady=(2,12))
        ctk.CTkLabel(box,text="Mot de passe",anchor="w",text_color=C["txt"]).grid(row=4,column=0,sticky="w",padx=35)
        _pf,self._ep=_make_pwd_entry(box,width=330,height=40); _pf.grid(row=5,column=0,padx=35,pady=(2,20))
        ctk.CTkButton(box,text="Se connecter",width=330,height=42,fg_color=C["pri"],hover_color=C["pri_h"],command=self._login).grid(row=6,column=0,padx=35,pady=(0,10))
        ctk.CTkButton(box,text="Créer un compte",width=330,height=36,fg_color="transparent",text_color=C["pri"],hover_color=C["border"],command=self._app.go_register).grid(row=7,column=0,padx=35)
        ctk.CTkButton(box,text="Mot de passe oublié ?",width=330,height=30,fg_color="transparent",text_color=C["txt2"],hover_color=C["border"],font=ctk.CTkFont(size=10),command=self._forgot).grid(row=8,column=0,padx=35,pady=(6,0))
    def _login(self):
        u,p=self._eu.get().strip(),self._ep.get()
        if not u or not p: messagebox.showwarning("Requis","Veuillez remplir tous les champs."); return
        try:
            user=self._db.obtenir_utilisateur_par_nom(u)
            if not user or not user.verifier_mot_de_passe(p): messagebox.showerror("Erreur","Identifiant ou mot de passe incorrect."); return
            if user.must_change_password:
                new_pw=simpledialog.askstring("Changement obligatoire","Votre mot de passe est temporaire.\nVeuillez en choisir un nouveau :",show="*",parent=self)
                if not new_pw: messagebox.showwarning("Requis","Vous devez changer votre mot de passe."); return
                ok,msg=Utilisateur.valider_mot_de_passe(new_pw)
                if not ok: messagebox.showerror("Mot de passe faible",msg); return
                user.password_hash=Utilisateur.hasher_mot_de_passe(new_pw)
                user.must_change_password=False
                self._db.modifier_utilisateur(user)
                try: self._db.ajouter_action(HistoriqueAction(utilisateur=user.username,action="Réinitialisation MDP",description=f"MDP changé (obligatoire) pour {user.username}",cible=user.id))
                except: pass
                messagebox.showinfo("Succès","Mot de passe mis à jour avec succès !")
            self._app.user=user; self._app.log_action("Connexion",f"Connexion de {user.username}",user.id); self._app.go_dash()
        except Exception as e: messagebox.showerror("Erreur",str(e))
    def _forgot(self):
        """Récupération de mot de passe avec champs masqués (email, réponse, nouveau MDP)."""
        # Étape 1 : Saisie de l'email (masqué avec possibilité de démasquer)
        email_val = self._ask_masked("Récupération", "Entrez votre adresse e-mail :")
        if not email_val or not email_val.strip(): return
        try:
            user=self._db.obtenir_utilisateur_par_email(email_val.strip())
            if not user: messagebox.showerror("Erreur","Aucun compte associé à cet email."); return
            if user.security_question and user.security_answer_hash:
                # Étape 2 : Réponse à la question de sécurité (masquée)
                reponse = self._ask_masked("Question de sécurité", f"Question : {user.security_question}\n\nVotre réponse :")
                if not reponse: return
                if not user.verifier_reponse_securite(reponse):
                    messagebox.showerror("Erreur","Réponse incorrecte."); return
                # Étape 3 : Nouveau mot de passe (masqué)
                new_pw = self._ask_masked("Nouveau mot de passe", "Saisissez votre nouveau mot de passe :")
                if not new_pw: return
                ok,msg=Utilisateur.valider_mot_de_passe(new_pw)
                if not ok: messagebox.showerror("Mot de passe faible",msg); return
                user.password_hash=Utilisateur.hasher_mot_de_passe(new_pw)
                user.must_change_password=False
                self._db.modifier_utilisateur(user)
                self._app.log_action("Réinitialisation MDP",f"MDP réinitialisé via question de sécurité pour {user.username}",user.id)
                messagebox.showinfo("Succès","Mot de passe réinitialisé avec succès !\nVous pouvez vous connecter.")
            else:
                messagebox.showinfo("Récupération",
                    f"Compte trouvé !\n\n"
                    f"Nom d'utilisateur : {user.username}\n"
                    f"Rôle : {'Administrateur' if user.is_admin else 'Utilisateur'}\n\n"
                    f"⚠️ Aucune question de sécurité n'a été configurée pour ce compte.\n\n"
                    f"Pour pouvoir récupérer votre mot de passe à l'avenir :\n"
                    f"• Connectez-vous puis utilisez « 🔑 Changer mot de passe »\n\n"
                    f"Si vous ne pouvez plus vous connecter :\n"
                    f"• Contactez un administrateur pour qu'il réinitialise votre mot de passe.")
        except Exception as e: messagebox.showerror("Erreur",str(e))

    def _ask_masked(self, title, prompt):
        """Boîte de dialogue avec champ masqué et bouton œil pour afficher/masquer."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("420x200")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)
        result = [None]
        ctk.CTkLabel(dialog, text=prompt, text_color=C["txt"], font=ctk.CTkFont(size=11), wraplength=380, justify="left").grid(row=0, column=0, padx=20, pady=(18, 8), sticky="w")
        entry_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        entry_frame.grid(row=1, column=0, padx=20, pady=(0, 10))
        entry_frame.grid_columnconfigure(0, weight=1)
        entry = ctk.CTkEntry(entry_frame, width=310, height=38, show="*")
        entry.grid(row=0, column=0, sticky="ew")
        vis = [False]
        def _toggle():
            vis[0] = not vis[0]
            entry.configure(show="" if vis[0] else "*")
            eye_btn.configure(text="🙈" if vis[0] else "👁")
        eye_btn = ctk.CTkButton(entry_frame, text="👁", width=36, height=38, fg_color="transparent", hover_color="#E2E8F0", text_color="#64748B", font=ctk.CTkFont(size=14), command=_toggle)
        eye_btn.grid(row=0, column=1, padx=(4, 0))
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=(0, 14))
        def _ok():
            result[0] = entry.get()
            dialog.destroy()
        def _cancel():
            dialog.destroy()
        ctk.CTkButton(btn_frame, text="Valider", width=120, height=36, fg_color=C["pri"], hover_color=C["pri_h"], command=_ok).grid(row=0, column=0, padx=6)
        ctk.CTkButton(btn_frame, text="Annuler", width=100, height=36, fg_color=C["txt2"], command=_cancel).grid(row=0, column=1, padx=6)
        entry.bind("<Return>", lambda e: _ok())
        entry.focus_set()
        dialog.wait_window()
        return result[0]

class RegisterFrame(ctk.CTkFrame):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_rowconfigure(0,weight=1); self.grid_columnconfigure(0,weight=1)
        box=ctk.CTkFrame(self,fg_color=C["card"],corner_radius=16,width=440,height=680); box.grid(row=0,column=0); box.grid_propagate(False); box.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(box,text="Créer un compte",font=ctk.CTkFont(size=22,weight="bold"),text_color=C["pri"]).grid(row=0,column=0,pady=(30,18))
        self._e={}
        for i,(lbl,k,sec) in enumerate([("Nom d'utilisateur","user",False),("E-mail (xxxx@xxxx.xxxx)","email",False),("Mot de passe","pwd",True),("Confirmer le mot de passe","pwd2",True)]):
            ctk.CTkLabel(box,text=lbl,anchor="w",text_color=C["txt"]).grid(row=1+i*2,column=0,sticky="w",padx=45)
            if sec:
                _pf,e=_make_pwd_entry(box,width=330,height=38); _pf.grid(row=2+i*2,column=0,padx=45,pady=(2,6))
            else:
                e=ctk.CTkEntry(box,width=330,height=38); e.grid(row=2+i*2,column=0,padx=45,pady=(2,6))
            self._e[k]=e
        ctk.CTkLabel(box,text="Question de sécurité",anchor="w",text_color=C["txt"]).grid(row=9,column=0,sticky="w",padx=45)
        self._e["secq"]=ctk.CTkComboBox(box,values=["Nom de votre premier animal ?","Ville de naissance de votre mère ?","Nom de votre meilleur ami d'enfance ?","Votre plat préféré ?"],width=330,height=32)
        self._e["secq"].grid(row=10,column=0,padx=45,pady=(2,4))
        ctk.CTkLabel(box,text="Réponse (à mémoriser)",anchor="w",text_color=C["txt"]).grid(row=11,column=0,sticky="w",padx=45)
        self._e["seca"]=ctk.CTkEntry(box,width=330,height=32,placeholder_text="Votre réponse secrète")
        self._e["seca"].grid(row=12,column=0,padx=45,pady=(2,6))
        ctk.CTkButton(box,text="Créer",width=330,height=42,fg_color=C["sec"],hover_color=C["sec_h"],command=self._create).grid(row=13,column=0,padx=45,pady=(8,6))
        ctk.CTkButton(box,text="Retour",width=330,height=36,fg_color="transparent",text_color=C["pri"],hover_color=C["border"],command=self._app.go_login).grid(row=14,column=0,padx=45)
    def _create(self):
        u,em,p,p2=[self._e[k].get().strip() for k in ("user","email","pwd","pwd2")]
        if not all([u,em,p,p2]): messagebox.showwarning("Requis","Veuillez remplir tous les champs."); return
        ok_em, msg_em = Utilisateur.valider_email(em)
        if not ok_em: messagebox.showerror("E-mail invalide",msg_em); return
        if p!=p2: messagebox.showerror("Erreur","Les mots de passe ne correspondent pas."); return
        ok,msg=Utilisateur.valider_mot_de_passe(p)
        if not ok: messagebox.showerror("Faible",msg); return
        try:
            if self._db.obtenir_utilisateur_par_nom(u): messagebox.showerror("Erreur","Ce nom d'utilisateur est déjà pris."); return
            secq=self._e["secq"].get().strip(); seca=self._e["seca"].get().strip()
            seca_hash=Utilisateur.hasher_mot_de_passe(seca.lower()) if seca else ""
            user=Utilisateur(username=u,email=em,password_hash=Utilisateur.hasher_mot_de_passe(p),security_question=secq,security_answer_hash=seca_hash)
            self._db.ajouter_utilisateur(user)
            try: self._db.ajouter_action(HistoriqueAction(utilisateur=u,action="Création compte",description=f"Compte « {u} » créé",cible=user.id))
            except: pass
            messagebox.showinfo("OK","Compte créé avec succès !"); self._app.go_login()
        except Exception as e: messagebox.showerror("Erreur",str(e))

class DashboardFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="dash")
        main=ctk.CTkScrollableFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=18,pady=18); main.grid_columnconfigure((0,1,2),weight=1)
        ctk.CTkLabel(main,text="Tableau de bord",font=ctk.CTkFont(size=22,weight="bold"),text_color=C["txt"]).grid(row=0,column=0,columnspan=3,sticky="w",pady=(0,12))
        try: s=db.statistiques()
        except: s={}
        try: sj=db.statistiques_jour()
        except: sj={}
        cards=[("💊 Produits",str(s.get("nb_produits",0)),C["pri"]),("📁 Catégories",str(s.get("nb_categories",0)),"#8B5CF6"),("🛒 Ventes du jour",str(sj.get("nb_ventes_jour",0)),C["sec"]),("💰 CA du jour",f'{sj.get("ca_jour",0):,.0f} FCFA',"#F59E0B"),("📉 Stock bas",str(s.get("nb_stock_bas",0)),C["warn"]),("🚫 Rupture",str(s.get("nb_rupture",0)),C["danger"])]
        for i,(t,v,col) in enumerate(cards):
            r,cc=divmod(i,3)
            f=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12,height=95); f.grid(row=r+1,column=cc,padx=5,pady=5,sticky="nsew"); f.grid_columnconfigure(0,weight=1)
            ctk.CTkLabel(f,text=t,font=ctk.CTkFont(size=11),text_color=C["txt2"]).grid(row=0,column=0,padx=12,pady=(10,2),sticky="w")
            ctk.CTkLabel(f,text=v,font=ctk.CTkFont(size=20,weight="bold"),text_color=col).grid(row=1,column=0,padx=12,pady=(0,10),sticky="w")
        nb_per=s.get("nb_lots_perimes",0)
        if nb_per>0:
            af=ctk.CTkFrame(main,fg_color="#FEE2E2",corner_radius=10); af.grid(row=3,column=0,columnspan=3,sticky="ew",padx=5,pady=5); af.grid_columnconfigure(0,weight=1)
            ctk.CTkLabel(af,text=f"ATTENTION: {nb_per} lot(s) périmé(s) ! Vente bloquée.",font=ctk.CTkFont(size=12,weight="bold"),text_color=C["danger"]).grid(row=0,column=0,padx=12,pady=8,sticky="w")
            ctk.CTkButton(af,text="Voir",width=70,height=28,fg_color=C["danger"],command=master.go_peremption).grid(row=0,column=1,padx=12)
        ctk.CTkLabel(main,text="Dernières ventes du jour",font=ctk.CTkFont(size=14,weight="bold"),text_color=C["txt"]).grid(row=4,column=0,columnspan=3,sticky="w",pady=(12,6))
        try:
            from datetime import datetime as dt_cls
            now=dt_cls.now()
            if now.hour<5: jour_5h=(now-timedelta(days=1)).strftime("%Y-%m-%dT05:00:00")
            else: jour_5h=now.strftime("%Y-%m-%dT05:00:00")
            ventes=[v for v in db.lister_ventes() if v.date_vente>=jour_5h][:8]
        except: ventes=[]
        for i,v in enumerate(ventes):
            dt=v.date_vente[:16].replace("T"," "); lbl=v.produit_nom or f"{len(v.lignes)} article(s)"
            ann=" [Annulée]" if v.annulee else ""
            lbl=f"{lbl}{ann}"
            lf=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=6,height=38); lf.grid(row=5+i,column=0,columnspan=3,sticky="ew",pady=1,padx=3); lf.grid_columnconfigure(1,weight=1)
            ctk.CTkLabel(lf,text=lbl,font=ctk.CTkFont(size=11),text_color=C["txt"]).grid(row=0,column=0,padx=10,pady=6,sticky="w")
            ctk.CTkLabel(lf,text=v.client_nom or "Anonyme",text_color=C["txt2"],font=ctk.CTkFont(size=10)).grid(row=0,column=1,sticky="w")
            ctk.CTkLabel(lf,text=f"{v.montant_total:,.0f} FCFA",font=ctk.CTkFont(size=11,weight="bold"),text_color=C["sec"]).grid(row=0,column=2,padx=8,sticky="e")
            ctk.CTkLabel(lf,text=dt,text_color=C["txt2"],font=ctk.CTkFont(size=9)).grid(row=0,column=3,padx=(0,10),sticky="e")

class CategoriesFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="adm_cat")
        main=ctk.CTkFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=18,pady=18); main.grid_columnconfigure(0,weight=1); main.grid_rowconfigure(2,weight=1)
        ctk.CTkLabel(main,text="Gestion des catégories",font=ctk.CTkFont(size=22,weight="bold"),text_color=C["txt"]).grid(row=0,column=0,sticky="w",pady=(0,10))
        ab=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); ab.grid(row=1,column=0,sticky="ew",pady=(0,10))
        ctk.CTkLabel(ab,text="Nouvelle catégorie :",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=0,column=0,padx=16,pady=10,sticky="w")
        self._en=ctk.CTkEntry(ab,width=250,height=34,placeholder_text="Nom"); self._en.grid(row=0,column=1,padx=4,pady=10)
        ctk.CTkButton(ab,text="+ Ajouter",width=100,height=34,fg_color=C["sec"],hover_color=C["sec_h"],command=self._add).grid(row=0,column=2,padx=16,pady=10)
        self._scroll=ctk.CTkScrollableFrame(main,fg_color=C["bg"]); self._scroll.grid(row=2,column=0,sticky="nsew"); self._scroll.grid_columnconfigure(0,weight=1)
        self._load()
        ctk.CTkButton(main,text="Retour à l'administration",width=120,height=34,fg_color=C["admin"],command=master.go_admin).grid(row=3,column=0,pady=10,sticky="w")
    def _load(self):
        for w in self._scroll.winfo_children(): w.destroy()
        try: cats=self._db.lister_categories()
        except: cats=[]
        if not cats: ctk.CTkLabel(self._scroll,text="Aucune catégorie.",text_color=C["txt2"]).grid(pady=30); return
        for i,c in enumerate(cats):
            bg=C["card"] if i%2==0 else "#F1F5F9"
            rf=ctk.CTkFrame(self._scroll,fg_color=bg,corner_radius=5,height=38); rf.grid(row=i,column=0,sticky="ew",pady=1); rf.grid_columnconfigure(0,weight=1)
            ctk.CTkLabel(rf,text=c.nom,font=ctk.CTkFont(size=12),text_color=C["txt"]).grid(row=0,column=0,padx=14,pady=8,sticky="w")
            af=ctk.CTkFrame(rf,fg_color="transparent"); af.grid(row=0,column=1,padx=8)
            cid=c.id; cnom=c.nom
            ctk.CTkButton(af,text="Renommer",width=70,height=26,font=ctk.CTkFont(size=9),fg_color=C["pri"],command=lambda _id=cid,_n=cnom:self._rename(_id,_n)).grid(row=0,column=0,padx=2)
            ctk.CTkButton(af,text="Suppr.",width=55,height=26,font=ctk.CTkFont(size=9),fg_color=C["danger"],command=lambda _id=cid:self._del(_id)).grid(row=0,column=1,padx=2)
    def _add(self):
        nom=self._en.get().strip()
        if not nom: messagebox.showwarning("Requis","Le nom est requis."); return
        try: self._db.ajouter_categorie(Categorie(nom=nom)); self._app.log_action("Ajout catégorie",f"Catégorie {nom} ajoutée"); self._en.delete(0,"end"); self._load()
        except Exception as e: messagebox.showerror("Erreur",str(e))
    def _rename(self,cid,old):
        new=simpledialog.askstring("Renommer",f"Nouveau nom pour '{old}':",initialvalue=old,parent=self)
        if new and new.strip():
            try: c=Categorie(nom=new.strip(),id_entite=cid); self._db.modifier_categorie(c); self._app.log_action("Modif catégorie",f"{old} -> {new.strip()}"); self._load()
            except Exception as e: messagebox.showerror("Erreur",str(e))
    def _del(self,cid):
        if messagebox.askyesno("Confirmer","Supprimer cette catégorie ?"):
            try: self._db.supprimer_categorie(cid); self._app.log_action("Suppr catégorie","Catégorie supprimée",cid); self._load()
            except Exception as e: messagebox.showerror("Erreur",str(e))

class ProduitsFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="prod")
        main=ctk.CTkFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=16,pady=16); main.grid_columnconfigure(0,weight=1); main.grid_rowconfigure(3,weight=1)
        ctk.CTkLabel(main,text="Produits",font=ctk.CTkFont(size=22,weight="bold"),text_color=C["txt"]).grid(row=0,column=0,sticky="w",pady=(0,8))
        filt=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=10); filt.grid(row=1,column=0,sticky="ew",pady=(0,6))
        ctk.CTkLabel(filt,text="Recherche :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=0,column=0,padx=(12,4),pady=6)
        self._sv=StringVar(); ctk.CTkEntry(filt,textvariable=self._sv,width=180,height=30,placeholder_text="Nom ou catégorie").grid(row=0,column=1,padx=2,pady=6)
        ctk.CTkLabel(filt,text="Catégorie :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=0,column=2,padx=(8,4))
        try: cats=db.lister_categories()
        except: cats=[]
        self._cats=cats; self._cats_map={c.id:c.nom for c in cats}
        self._fcat=ctk.CTkComboBox(filt,values=["Toutes"]+[c.nom for c in cats],width=130,height=30); self._fcat.grid(row=0,column=3,padx=2)
        ctk.CTkLabel(filt,text="Ordonnance :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=0,column=4,padx=(8,4))
        self._fordo=ctk.CTkComboBox(filt,values=["Tous","Oui","Non"],width=75,height=30); self._fordo.grid(row=0,column=5,padx=2)
        ctk.CTkLabel(filt,text="Statut stock :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=1,column=0,padx=(12,4),pady=(0,6))
        self._fstock=ctk.CTkComboBox(filt,values=["Tous","Rupture","Bas","Normal"],width=100,height=30); self._fstock.grid(row=1,column=1,padx=2,pady=(0,6))
        ctk.CTkLabel(filt,text="Tri stock vendable :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=1,column=2,padx=(8,4),pady=(0,6))
        self._ftri=ctk.CTkComboBox(filt,values=["Aucun","Croissant","Décroissant"],width=110,height=30); self._ftri.grid(row=1,column=3,padx=2,pady=(0,6))
        ctk.CTkButton(filt,text="Filtrer",width=70,height=30,fg_color=C["pri"],command=self._load).grid(row=0,column=6,padx=(8,12),rowspan=2)
        th=ctk.CTkFrame(main,fg_color=C["pri"],corner_radius=8,height=34); th.grid(row=2,column=0,sticky="ew",pady=(4,0)); th.grid_columnconfigure((0,1,2,3,4,5,6),weight=1)
        for i,h in enumerate(["Nom","Catégorie","Prix","Stock vendable","Stock total","Ordo","Actions"]):
            ctk.CTkLabel(th,text=h,font=ctk.CTkFont(size=10,weight="bold"),text_color="white").grid(row=0,column=i,padx=4,pady=6)
        self._scroll=ctk.CTkScrollableFrame(main,fg_color=C["bg"]); self._scroll.grid(row=3,column=0,sticky="nsew"); self._scroll.grid_columnconfigure((0,1,2,3,4,5,6),weight=1)
        self._load()
    def _load(self):
        for w in self._scroll.winfo_children(): w.destroy()
        terme=self._sv.get().strip(); cat_nom=self._fcat.get(); ordo_v=self._fordo.get().lower()
        cat_id=""
        if cat_nom!="Toutes": cat_id=next((c.id for c in self._cats if c.nom==cat_nom),"")
        ordo="" if ordo_v=="tous" else ordo_v
        try: prods=self._db.filtrer_produits(terme=terme,categorie_id=cat_id,ordo=ordo)
        except: prods=[]
        # Calculer stock vendable pour chaque produit
        prods_info=[]
        for p in prods:
            try: sd=self._db.stock_details(p.id)
            except: sd={"stock_total":p.quantite,"stock_perime":0,"stock_vendable":p.quantite}
            prods_info.append((p,sd))
        # Filtrer par statut de stock (basé sur stock vendable)
        fstock=self._fstock.get() if hasattr(self,'_fstock') else "Tous"
        if fstock=="Rupture":
            prods_info=[(p,sd) for p,sd in prods_info if sd["stock_vendable"]==0]
        elif fstock=="Bas":
            prods_info=[(p,sd) for p,sd in prods_info if 0<sd["stock_vendable"]<=10]
        elif fstock=="Normal":
            prods_info=[(p,sd) for p,sd in prods_info if sd["stock_vendable"]>10]
        # Tri par stock vendable
        ftri=self._ftri.get() if hasattr(self,'_ftri') else "Aucun"
        if ftri=="Croissant":
            prods_info.sort(key=lambda x:x[1]["stock_vendable"])
        elif ftri=="Décroissant":
            prods_info.sort(key=lambda x:x[1]["stock_vendable"],reverse=True)
        if not prods_info: ctk.CTkLabel(self._scroll,text="Aucun produit trouvé.",text_color=C["txt2"]).grid(row=0,column=0,columnspan=7,pady=30); return
        for i,(p,sd) in enumerate(prods_info):
            bg=C["card"] if i%2==0 else "#F1F5F9"
            rf=ctk.CTkFrame(self._scroll,fg_color=bg,corner_radius=5,height=36); rf.grid(row=i,column=0,columnspan=7,sticky="ew",pady=1); rf.grid_columnconfigure((0,1,2,3,4,5,6),weight=1)
            cat=self._cats_map.get(p.categorie_id,"-")
            nl=ctk.CTkLabel(rf,text=p.nom,font=ctk.CTkFont(size=10),text_color=C["pri"],cursor="hand2"); nl.grid(row=0,column=0,padx=5,pady=6)
            nl.bind("<Button-1>",lambda e,pid=p.id:self._app.go_detail(pid))
            ctk.CTkLabel(rf,text=cat,font=ctk.CTkFont(size=10),text_color=C["txt2"]).grid(row=0,column=1,padx=4)
            ctk.CTkLabel(rf,text=f"{p.prix:,.0f}",font=ctk.CTkFont(size=10,weight="bold"),text_color=C["txt"]).grid(row=0,column=2,padx=4)
            sv=sd["stock_vendable"]
            sv_col="red" if sv==0 else ("orange" if sv<=10 else "green")
            ctk.CTkLabel(rf,text=str(sv),font=ctk.CTkFont(size=10,weight="bold"),text_color=sv_col).grid(row=0,column=3,padx=4)
            st_txt=f"{sd['stock_total']}"
            if sd["stock_perime"]>0: st_txt+=f" ({sd['stock_perime']} pér.)"
            ctk.CTkLabel(rf,text=st_txt,font=ctk.CTkFont(size=10),text_color=C["txt2"]).grid(row=0,column=4,padx=4)
            ctk.CTkLabel(rf,text="Oui" if p.sur_ordonnance else "Non",font=ctk.CTkFont(size=10),text_color=C["admin"] if p.sur_ordonnance else C["txt2"]).grid(row=0,column=5,padx=4)
            af=ctk.CTkFrame(rf,fg_color="transparent"); af.grid(row=0,column=6,padx=2); pid=p.id
            ctk.CTkButton(af,text="Edit",width=42,height=24,font=ctk.CTkFont(size=9),fg_color=C["pri"],command=lambda _=pid:self._app.go_modif(_)).grid(row=0,column=0,padx=1)
            ctk.CTkButton(af,text="Suppr.",width=42,height=24,font=ctk.CTkFont(size=9),fg_color=C["danger"],command=lambda _=pid:self._del(_)).grid(row=0,column=1,padx=1)
    def _del(self,pid):
        if messagebox.askyesno("Confirmer","Supprimer ce produit ?"):
            try: self._db.supprimer_produit(pid); self._app.log_action("Suppression","Produit supprime",pid); self._load()
            except Exception as e: messagebox.showerror("Erreur",str(e))

class DetailProduitFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,produit_id="",**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="prod")
        main=ctk.CTkScrollableFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=20,pady=20); main.grid_columnconfigure(0,weight=1)
        try: p=db.obtenir_produit(produit_id); cats={c.id:c.nom for c in db.lister_categories()}
        except: p=None; cats={}
        if not p: ctk.CTkLabel(main,text="Produit introuvable.",text_color=C["danger"]).grid(pady=30); return
        ctk.CTkLabel(main,text=p.nom,font=ctk.CTkFont(size=24,weight="bold"),text_color=C["pri"]).grid(row=0,column=0,sticky="w",pady=(0,10))
        box=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); box.grid(row=1,column=0,sticky="ew"); box.grid_columnconfigure((0,1),weight=1)
        try: sd=db.stock_details(produit_id)
        except: sd={"stock_total":p.quantite,"stock_perime":0,"stock_vendable":p.quantite}
        infos=[("Catégorie",cats.get(p.categorie_id,"")),("Prix",f"{p.prix:,.0f} FCFA"),("Stock total",str(sd["stock_total"])),("Stock périmé",str(sd["stock_perime"])),("Stock vendable (non périmé)",str(sd["stock_vendable"])),("Sur ordonnance","Oui" if p.sur_ordonnance else "Non")]
        for i,(lbl,val) in enumerate(infos):
            r,c2=divmod(i,2)
            ctk.CTkLabel(box,text=f"{lbl}: {val}",text_color=C["txt"],font=ctk.CTkFont(size=12)).grid(row=r,column=c2,sticky="w",padx=18,pady=8)
        try: arrs=db.lister_arrivages(produit_id)
        except: arrs=[]
        lots_actifs=[a for a in arrs if a.quantite_restante>0]
        ctk.CTkLabel(box,text=f"Nombre de lots actifs: {len(lots_actifs)}",text_color=C["txt"],font=ctk.CTkFont(size=12,weight="bold")).grid(row=4,column=0,columnspan=2,sticky="w",padx=18,pady=(12,4))
        if lots_actifs:
            lh=ctk.CTkFrame(box,fg_color=C["pri"],corner_radius=6,height=28); lh.grid(row=5,column=0,columnspan=2,sticky="ew",padx=18,pady=(4,2)); lh.grid_columnconfigure((0,1,2,3),weight=1)
            for j,h in enumerate(["Date arrivage","Stock restant","Péremption","Fournisseur"]):
                ctk.CTkLabel(lh,text=h,font=ctk.CTkFont(size=9,weight="bold"),text_color="white").grid(row=0,column=j,padx=4,pady=4)
            for ii,a in enumerate(lots_actifs):
                bgc="#FEE2E2" if a.est_perime() else C["card"]
                lff=ctk.CTkFrame(box,fg_color=bgc,corner_radius=4); lff.grid(row=6+ii,column=0,columnspan=2,sticky="ew",padx=18,pady=1); lff.grid_columnconfigure((0,1,2,3),weight=1)
                ctk.CTkLabel(lff,text=a.date_arrivage[:10],font=ctk.CTkFont(size=10),text_color=C["txt"]).grid(row=0,column=0,padx=6,pady=4)
                ctk.CTkLabel(lff,text=str(a.quantite_restante),font=ctk.CTkFont(size=10,weight="bold"),text_color=C["txt"]).grid(row=0,column=1,padx=6,pady=4)
                exp_col=C["danger"] if a.est_perime() else C["txt2"]
                ctk.CTkLabel(lff,text=a.date_peremption or "N/A",font=ctk.CTkFont(size=10),text_color=exp_col).grid(row=0,column=2,padx=6,pady=4)
                ctk.CTkLabel(lff,text=a.fournisseur,font=ctk.CTkFont(size=10),text_color=C["txt2"]).grid(row=0,column=3,padx=6,pady=4)
        else:
            ctk.CTkLabel(box,text="Aucun lot actif.",text_color=C["txt2"]).grid(row=6,column=0,columnspan=2,padx=18,pady=8,sticky="w")
        ctk.CTkButton(main,text="Retour",width=120,height=36,fg_color=C["pri"],command=master.go_produits).grid(row=2,column=0,pady=15,sticky="w")

class AjoutProduitFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="adm_ajout")
        main=ctk.CTkFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=22,pady=22); main.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(main,text="Ajouter un produit",font=ctk.CTkFont(size=22,weight="bold"),text_color=C["admin"]).grid(row=0,column=0,sticky="w",pady=(0,12))
        box=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); box.grid(row=1,column=0,sticky="ew"); box.grid_columnconfigure((0,1),weight=1)
        ctk.CTkLabel(box,text="Nom du produit",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=0,column=0,sticky="w",padx=16,pady=(12,2))
        self._enom=ctk.CTkEntry(box,width=270,height=34,placeholder_text="Nom"); self._enom.grid(row=1,column=0,padx=16,sticky="w")
        ctk.CTkLabel(box,text="Prix (FCFA)",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=0,column=1,sticky="w",padx=16,pady=(12,2))
        self._eprix=ctk.CTkEntry(box,width=270,height=34,placeholder_text="Prix"); self._eprix.grid(row=1,column=1,padx=16,sticky="w")
        ctk.CTkLabel(box,text="Catégorie",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=2,column=0,sticky="w",padx=16,pady=(12,2))
        try: cats=db.lister_categories()
        except: cats=[]
        self._cats=cats
        self._combo=ctk.CTkComboBox(box,values=[c.nom for c in cats] or ["-"],width=270,height=34); self._combo.grid(row=3,column=0,padx=16,sticky="w")
        self._ov=ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(box,text="Sur ordonnance",variable=self._ov,font=ctk.CTkFont(size=11)).grid(row=3,column=1,padx=16,pady=10,sticky="w")
        ctk.CTkLabel(box,text="NB : La quantité et la date d'expiration sont gérées via les arrivages.",text_color=C["warn"],font=ctk.CTkFont(size=10),wraplength=500).grid(row=4,column=0,columnspan=2,padx=16,pady=(6,4),sticky="w")
        bf=ctk.CTkFrame(box,fg_color="transparent"); bf.grid(row=5,column=0,columnspan=2,pady=16)
        ctk.CTkButton(bf,text="Enregistrer",width=150,height=38,fg_color=C["sec"],hover_color=C["sec_h"],command=self._save).grid(row=0,column=0,padx=8)
        ctk.CTkButton(bf,text="Retour à l'administration",width=100,height=38,fg_color=C["admin"],command=master.go_admin).grid(row=0,column=1,padx=8)
    def _save(self):
        try:
            nom=self._enom.get().strip(); prix_s=self._eprix.get().strip(); cn=self._combo.get()
            if not nom or not prix_s: messagebox.showwarning("Requis","Nom et prix obligatoires."); return
            prix=float(prix_s); cid=next((c.id for c in self._cats if c.nom==cn),"")
            if not cid: messagebox.showerror("Erreur","Catégorie invalide."); return
            p=Produit(nom=nom,categorie_id=cid,prix=prix,sur_ordonnance=self._ov.get())
            self._db.ajouter_produit(p); self._app.log_action("Ajout produit",f"Ajout {nom} prix={prix}",p.id)
            messagebox.showinfo("OK",f"{nom} ajouté ! Enregistrez un arrivage pour ce produit."); self._app.go_admin_arrivage()
        except ValueError as e: messagebox.showerror("Saisie",str(e))
        except Exception as e: messagebox.showerror("Erreur",str(e))

class ModifProduitFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,produit_id="",**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db,self._pid=master,db,produit_id
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="prod")
        main=ctk.CTkFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=22,pady=22); main.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(main,text="Modifier le produit",font=ctk.CTkFont(size=22,weight="bold"),text_color=C["txt"]).grid(row=0,column=0,sticky="w",pady=(0,12))
        box=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); box.grid(row=1,column=0,sticky="ew"); box.grid_columnconfigure((0,1),weight=1)
        try: prod=db.obtenir_produit(produit_id); cats=db.lister_categories()
        except: prod=None; cats=[]
        if not prod: ctk.CTkLabel(box,text="Introuvable.",text_color=C["danger"]).grid(padx=20,pady=20); return
        self._cats=cats; self._ent={}
        for lbl,k,val,col in [("Nom","nom",prod.nom,0),("Prix","prix",str(int(prod.prix)),1)]:
            ctk.CTkLabel(box,text=lbl,text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=0,column=col,sticky="w",padx=16,pady=(12,2))
            e=ctk.CTkEntry(box,width=270,height=34); e.insert(0,val); e.grid(row=1,column=col,padx=16,sticky="w"); self._ent[k]=e
        ctk.CTkLabel(box,text="Catégorie",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=2,column=0,sticky="w",padx=16,pady=(12,2))
        cur_cat=next((c.nom for c in cats if c.id==prod.categorie_id),"")
        self._combo=ctk.CTkComboBox(box,values=[c.nom for c in cats],width=270,height=34)
        if cur_cat: self._combo.set(cur_cat)
        self._combo.grid(row=3,column=0,padx=16,sticky="w")
        self._ov=ctk.BooleanVar(value=prod.sur_ordonnance)
        ctk.CTkCheckBox(box,text="Sur ordonnance",variable=self._ov,font=ctk.CTkFont(size=11)).grid(row=3,column=1,padx=16,pady=10,sticky="w")
        ctk.CTkLabel(box,text="Description de la modification (OBLIGATOIRE)",text_color=C["danger"],font=ctk.CTkFont(size=11,weight="bold")).grid(row=4,column=0,columnspan=2,sticky="w",padx=16,pady=(12,2))
        self._edesc=ctk.CTkEntry(box,width=560,height=34,placeholder_text="Décrivez la modification..."); self._edesc.grid(row=5,column=0,columnspan=2,padx=16,sticky="w",pady=(0,10))
        bf=ctk.CTkFrame(box,fg_color="transparent"); bf.grid(row=6,column=0,columnspan=2,pady=16)
        ctk.CTkButton(bf,text="Sauvegarder",width=150,height=38,fg_color=C["pri"],command=self._save).grid(row=0,column=0,padx=8)
        ctk.CTkButton(bf,text="Annuler",width=100,height=38,fg_color=C["txt2"],command=master.go_produits).grid(row=0,column=1,padx=8)
    def _save(self):
        desc=self._edesc.get().strip()
        if not desc: messagebox.showerror("Requis","La description de la modification est obligatoire."); return
        try:
            nom=self._ent["nom"].get().strip(); prix=float(self._ent["prix"].get().strip()); cn=self._combo.get()
            cid=next((c.id for c in self._cats if c.nom==cn),"")
            if not cid: messagebox.showerror("Erreur","Catégorie invalide."); return
            old=self._db.obtenir_produit(self._pid)
            p=Produit(nom=nom,categorie_id=cid,prix=prix,quantite=old.quantite,description=old.description,date_expiration=old.date_expiration,sur_ordonnance=self._ov.get(),id_entite=self._pid)
            self._db.modifier_produit(p); self._app.log_action("Modification produit",desc,self._pid)
            messagebox.showinfo("OK","Produit modifié avec succès !"); self._app.go_produits()
        except Exception as e: messagebox.showerror("Erreur",str(e))

class VenteGroupeeFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="vgrp")
        main=ctk.CTkScrollableFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=20,pady=20); main.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(main,text="Nouvelle vente / Facturation groupée",font=ctk.CTkFont(size=20,weight="bold"),text_color=C["txt"]).grid(row=0,column=0,sticky="w",pady=(0,12))
        ib=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); ib.grid(row=1,column=0,sticky="ew",pady=(0,10)); ib.grid_columnconfigure((0,1),weight=1)
        ctk.CTkLabel(ib,text="Nom du client (optionnel, sauf ordonnance)",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=0,column=0,sticky="w",padx=16,pady=(12,2))
        self._ec=ctk.CTkEntry(ib,width=260,height=34,placeholder_text="Client (optionnel)"); self._ec.grid(row=1,column=0,padx=16,pady=(0,10),sticky="w")
        ctk.CTkLabel(ib,text="Structure hospitalière (si ordonnance)",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=0,column=1,sticky="w",padx=16,pady=(12,2))
        self._es=ctk.CTkEntry(ib,width=260,height=34,placeholder_text="Hôpital / Clinique"); self._es.grid(row=1,column=1,padx=16,pady=(0,10),sticky="w")
        ab=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); ab.grid(row=2,column=0,sticky="ew",pady=(0,10)); ab.grid_columnconfigure((0,1,2),weight=1)
        ctk.CTkLabel(ab,text="Ajouter un produit",font=ctk.CTkFont(size=12,weight="bold"),text_color=C["txt"]).grid(row=0,column=0,columnspan=3,sticky="w",padx=16,pady=(12,6))
        try: prods=db.lister_produits()
        except: prods=[]
        self._prods={p.nom:p for p in prods}
        self._cp=ctk.CTkComboBox(ab,values=[p.nom for p in prods] or ["-"],width=200,height=34,command=self._on_prod); self._cp.grid(row=1,column=0,padx=16,pady=(0,10),sticky="w")
        self._clot=ctk.CTkComboBox(ab,values=["-"],width=260,height=34); self._clot.grid(row=1,column=1,padx=4,pady=(0,10),sticky="w")
        self._eq=ctk.CTkEntry(ab,width=70,height=34,placeholder_text="Qte"); self._eq.grid(row=1,column=2,padx=4,pady=(0,10),sticky="w")
        ctk.CTkButton(ab,text="+ Ajouter",width=90,height=34,fg_color=C["sec"],hover_color=C["sec_h"],command=self._add_line).grid(row=1,column=3,padx=16,pady=(0,10),sticky="w")
        self._lots_data={}
        self._on_prod(self._cp.get() if prods else "")
        self._lignes=[]
        self._lf=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); self._lf.grid(row=3,column=0,sticky="ew",pady=(0,10)); self._lf.grid_columnconfigure(0,weight=1)
        self._tl=ctk.CTkLabel(main,text="Total : 0 FCFA",font=ctk.CTkFont(size=16,weight="bold"),text_color=C["sec"]); self._tl.grid(row=4,column=0,sticky="e",padx=20,pady=5)
        bf=ctk.CTkFrame(main,fg_color="transparent"); bf.grid(row=5,column=0,pady=10)
        ctk.CTkButton(bf,text="Valider la vente",width=170,height=40,fg_color=C["sec"],hover_color=C["sec_h"],command=self._validate).grid(row=0,column=0,padx=8)
        ctk.CTkButton(bf,text="Annuler",width=100,height=40,fg_color=C["txt2"],command=master.go_produits).grid(row=0,column=1,padx=8)
        self._rfl()
    def _on_prod(self,pn):
        self._lots_data={}
        p=self._prods.get(pn)
        if not p: self._clot.configure(values=["-"]); self._clot.set("-"); return
        try: lots=self._db.lister_lots_vendables(p.id)
        except: lots=[]
        if not lots: self._clot.configure(values=["Aucun lot disponible"]); self._clot.set("Aucun lot disponible"); return
        vals=[]
        for a in lots:
            exp=a.date_peremption or "sans exp."
            lbl=f"Lot {a.date_arrivage[:10]} | rest:{a.quantite_restante} | exp:{exp}"
            vals.append(lbl); self._lots_data[lbl]=a
        self._clot.configure(values=vals); self._clot.set(vals[0])
    def _add_line(self):
        pn=self._cp.get(); qs=self._eq.get().strip(); lot_key=self._clot.get()
        if not qs: messagebox.showwarning("Requis","Veuillez saisir une quantité."); return
        try: q=int(qs)
        except: messagebox.showerror("Erreur","Quantité invalide."); return
        if q<=0: messagebox.showerror("Erreur","La quantité doit être supérieure à 0."); return
        p=self._prods.get(pn)
        if not p: messagebox.showerror("Erreur","Produit introuvable."); return
        ok,msg=p.peut_etre_vendu()
        if not ok: messagebox.showerror("Interdit",msg); return
        arr=self._lots_data.get(lot_key)
        if not arr: messagebox.showerror("Erreur","Veuillez sélectionner un lot valide."); return
        deja=sum(l["quantite"] for l in self._lignes if l.get("arrivage_id")==arr.id)
        dispo=arr.quantite_restante-deja
        if q>dispo: messagebox.showerror("Stock lot",f"Stock insuffisant dans ce lot ({dispo} dispo)."); return
        self._lignes.append({"produit_id":p.id,"produit_nom":p.nom,"prix_unitaire":p.prix,"quantite":q,"sous_total":p.prix*q,"sur_ordonnance":p.sur_ordonnance,"arrivage_id":arr.id,"lot_info":f"exp:{arr.date_peremption or 'N/A'}"})
        self._eq.delete(0,"end"); self._rfl()
    def _rfl(self):
        for w in self._lf.winfo_children(): w.destroy()
        if not self._lignes:
            ctk.CTkLabel(self._lf,text="Aucun article ajouté.",text_color=C["txt2"]).grid(padx=16,pady=10)
        else:
            for i,l in enumerate(self._lignes):
                rf=ctk.CTkFrame(self._lf,fg_color=C["card"] if i%2==0 else "#F1F5F9",corner_radius=4); rf.grid(row=i,column=0,sticky="ew",pady=1); rf.grid_columnconfigure(0,weight=1)
                ot=" [ORDO]" if l.get("sur_ordonnance") else ""
                li=f" ({l.get('lot_info','')})" if l.get('lot_info') else ""
                ctk.CTkLabel(rf,text=f"{l['produit_nom']}{ot} x{l['quantite']} = {l['sous_total']:,.0f} FCFA{li}",font=ctk.CTkFont(size=11),text_color=C["txt"]).grid(row=0,column=0,padx=14,pady=6,sticky="w")
                ctk.CTkButton(rf,text="X",width=28,height=24,fg_color=C["danger"],font=ctk.CTkFont(size=9),command=lambda idx=i:self._rm(idx)).grid(row=0,column=1,padx=8)
        self._tl.configure(text=f"Total : {sum(l['sous_total'] for l in self._lignes):,.0f} FCFA")
    def _rm(self,idx): self._lignes.pop(idx); self._rfl()
    def _validate(self):
        if not self._lignes: messagebox.showwarning("Vide","Veuillez ajouter au moins un produit."); return
        has_ordo=any(l.get("sur_ordonnance") for l in self._lignes)
        cl=self._ec.get().strip(); struct=self._es.get().strip()
        if has_ordo:
            prods_ordo=list(set(l["produit_nom"] for l in self._lignes if l.get("sur_ordonnance")))
            if not cl: messagebox.showerror("Ordonnance",f"Nom client obligatoire.\nProduit(s) sur ordonnance: {', '.join(prods_ordo)}"); return
            if not struct: messagebox.showerror("Ordonnance",f"Structure hospitaliere obligatoire.\nProduit(s) sur ordonnance: {', '.join(prods_ordo)}"); return
        try:
            total=sum(l["sous_total"] for l in self._lignes)
            f1=self._lignes[0] if len(self._lignes)==1 else {}
            v=Vente(client_nom=cl,montant_total=total,lignes=self._lignes,structure_hospitaliere=struct,produit_id=f1.get("produit_id",""),produit_nom=f1.get("produit_nom",""),quantite=f1.get("quantite",0),prix_unitaire=f1.get("prix_unitaire",0))
            self._db.ajouter_vente(v)
            for l in self._lignes:
                arr_id=l.get("arrivage_id","")
                if arr_id:
                    arrs=self._db.lister_arrivages(l["produit_id"])
                    for a in arrs:
                        if a.id==arr_id: self._db.modifier_arrivage_qte_restante(arr_id,a.quantite_restante-l["quantite"]); break
                self._db.recalculer_stock_produit(l["produit_id"])
                self._db.supprimer_lots_vides(l["produit_id"])
                self._db.maj_description_produit_depuis_arrivages(l["produit_id"])
                self._db.ajouter_mouvement(MouvementStock(produit_id=l["produit_id"],produit_nom=l["produit_nom"],type_mvt="Vente",quantite=l["quantite"],description=f"Vente facture {v.id[:8]} lot:{arr_id[:8]}"))
            self._app.log_action("Vente",f"Facture {v.id[:8]} - {len(self._lignes)} art - {total:,.0f} FCFA",v.id)
            self._app.go_facture(v.id)
        except Exception as e: messagebox.showerror("Erreur",str(e))

class HistoVentesFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="histo")
        main=ctk.CTkFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=16,pady=16); main.grid_columnconfigure(0,weight=1); main.grid_rowconfigure(2,weight=1)
        ctk.CTkLabel(main,text="Historique des ventes",font=ctk.CTkFont(size=22,weight="bold"),text_color=C["txt"]).grid(row=0,column=0,sticky="w",pady=(0,10))
        th=ctk.CTkFrame(main,fg_color=C["pri"],corner_radius=8,height=34); th.grid(row=1,column=0,sticky="ew"); th.grid_columnconfigure((0,1,2,3,4,5),weight=1)
        for i,h in enumerate(["ID","Client","Articles","Montant","Date","Actions"]):
            ctk.CTkLabel(th,text=h,font=ctk.CTkFont(size=10,weight="bold"),text_color="white").grid(row=0,column=i,padx=5,pady=6)
        scroll=ctk.CTkScrollableFrame(main,fg_color=C["bg"]); scroll.grid(row=2,column=0,sticky="nsew"); scroll.grid_columnconfigure((0,1,2,3,4,5),weight=1)
        try: ventes=db.lister_ventes()
        except: ventes=[]
        if not ventes: ctk.CTkLabel(scroll,text="Aucune vente enregistrée.",text_color=C["txt2"]).grid(row=0,column=0,columnspan=6,pady=30)
        for i,v in enumerate(ventes):
            bg="#FEE2E2" if v.annulee else (C["card"] if i%2==0 else "#F1F5F9")
            rf=ctk.CTkFrame(scroll,fg_color=bg,corner_radius=5,height=34); rf.grid(row=i,column=0,columnspan=6,sticky="ew",pady=1); rf.grid_columnconfigure((0,1,2,3,4,5),weight=1)
            dt=v.date_vente[:16].replace("T"," "); arts=v.produit_nom if v.produit_nom else f"{len(v.lignes)} article(s)"
            ann=" [Annulée]" if v.annulee else ""
            for j,val in enumerate([v.id[:8]+"..",v.client_nom or "-",arts+ann,f"{v.montant_total:,.0f} FCFA",dt]):
                col=C["txt2"] if v.annulee else (C["sec"] if j==3 else C["txt"])
                ctk.CTkLabel(rf,text=val,font=ctk.CTkFont(size=10,weight="bold" if j==3 else "normal"),text_color=col).grid(row=0,column=j,padx=5,pady=5)
            vid=v.id
            ctk.CTkButton(rf,text="Detail",width=50,height=22,font=ctk.CTkFont(size=9),fg_color=C["pri"],command=lambda _v=vid:self._app.go_facture(_v)).grid(row=0,column=5,padx=4)

class FactureFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,vente_id="",**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="histo")
        main=ctk.CTkScrollableFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=22,pady=22); main.grid_columnconfigure(0,weight=1)
        vente=db.obtenir_vente(vente_id) if vente_id else None
        if not vente: ctk.CTkLabel(main,text="Facture introuvable.",text_color=C["danger"]).grid(pady=30); return
        ctk.CTkLabel(main,text="Vente enregistree !",font=ctk.CTkFont(size=20,weight="bold"),text_color=C["sec"]).grid(row=0,column=0,sticky="w",pady=(0,12))
        box=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); box.grid(row=1,column=0,sticky="ew"); box.grid_columnconfigure(0,weight=1)
        hdr=ctk.CTkFrame(box,fg_color=C["pri"],corner_radius=8); hdr.grid(row=0,column=0,sticky="ew",padx=16,pady=(16,10)); hdr.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(hdr,text="FACTURE / REÇU",font=ctk.CTkFont(size=15,weight="bold"),text_color="white").grid(row=0,column=0,padx=12,pady=8,sticky="w")
        ctk.CTkLabel(hdr,text=f"No {vente.id[:12]}",text_color="#BFDBFE",font=ctk.CTkFont(size=10)).grid(row=0,column=1,padx=12,sticky="e")
        r=1
        for lbl,val in [("Client",vente.client_nom or "-"),("Date",vente.date_vente[:19].replace("T"," "))]:
            ctk.CTkLabel(box,text=f"{lbl}: {val}",text_color=C["txt"],font=ctk.CTkFont(size=12)).grid(row=r,column=0,sticky="w",padx=20,pady=4); r+=1
        if vente.structure_hospitaliere:
            ctk.CTkLabel(box,text=f"Structure: {vente.structure_hospitaliere}",text_color=C["admin"],font=ctk.CTkFont(size=12,weight="bold")).grid(row=r,column=0,sticky="w",padx=20,pady=4); r+=1
        ctk.CTkFrame(box,fg_color=C["border"],height=1).grid(row=r,column=0,sticky="ew",padx=20,pady=8); r+=1
        lignes=vente.lignes if vente.lignes else [{"produit_nom":vente.produit_nom,"quantite":vente.quantite,"prix_unitaire":vente.prix_unitaire,"sous_total":vente.montant_total}]
        hf=ctk.CTkFrame(box,fg_color="#E2E8F0",corner_radius=4); hf.grid(row=r,column=0,sticky="ew",padx=20,pady=(0,2)); hf.grid_columnconfigure((0,1,2,3),weight=1)
        for j,h in enumerate(["Produit","Quantité","Prix unit.","Sous-total"]): ctk.CTkLabel(hf,text=h,font=ctk.CTkFont(size=10,weight="bold"),text_color=C["txt"]).grid(row=0,column=j,padx=6,pady=4)
        r+=1
        for l in lignes:
            lrf=ctk.CTkFrame(box,fg_color=C["card"],corner_radius=2); lrf.grid(row=r,column=0,sticky="ew",padx=20,pady=1); lrf.grid_columnconfigure((0,1,2,3),weight=1)
            ctk.CTkLabel(lrf,text=str(l.get("produit_nom","")),font=ctk.CTkFont(size=11),text_color=C["txt"]).grid(row=0,column=0,padx=6,pady=3)
            ctk.CTkLabel(lrf,text=str(l.get("quantite","")),font=ctk.CTkFont(size=11),text_color=C["txt"]).grid(row=0,column=1,padx=6,pady=3)
            ctk.CTkLabel(lrf,text=f'{l.get("prix_unitaire",0):,.0f} FCFA',font=ctk.CTkFont(size=11),text_color=C["txt"]).grid(row=0,column=2,padx=6,pady=3)
            ctk.CTkLabel(lrf,text=f'{l.get("sous_total",0):,.0f} FCFA',font=ctk.CTkFont(size=11,weight="bold"),text_color=C["sec"]).grid(row=0,column=3,padx=6,pady=3)
            r+=1
        ctk.CTkFrame(box,fg_color=C["border"],height=1).grid(row=r,column=0,sticky="ew",padx=20,pady=8); r+=1
        ctk.CTkLabel(box,text=f"TOTAL : {vente.montant_total:,.0f} FCFA",text_color=C["sec"],font=ctk.CTkFont(size=20,weight="bold")).grid(row=r,column=0,sticky="e",padx=20,pady=(0,6)); r+=1
        ctk.CTkLabel(box,text="Note : l'annulation est possible dans un délai de 3 h après la vente.",text_color=C["txt2"],font=ctk.CTkFont(size=9)).grid(row=r,column=0,sticky="w",padx=20,pady=(0,14))
        self._vente=vente
        bf=ctk.CTkFrame(main,fg_color="transparent"); bf.grid(row=2,column=0,pady=14)
        ctk.CTkButton(bf,text="Historique",width=100,height=36,fg_color=C["pri"],command=master.go_histo).grid(row=0,column=0,padx=6)
        ctk.CTkButton(bf,text="Dashboard",width=100,height=36,fg_color=C["txt2"],command=master.go_dash).grid(row=0,column=1,padx=6)
        ctk.CTkButton(bf,text="Export PDF",width=100,height=36,fg_color=C["admin"],command=lambda:self._pdf(vente)).grid(row=0,column=2,padx=6)
        if not vente.annulee:
            ctk.CTkButton(bf,text="Annuler la facture",width=120,height=36,fg_color=C["danger"],command=self._annuler).grid(row=0,column=3,padx=6)
    def _annuler(self):
        ok,msg=self._vente.peut_etre_annulee()
        if not ok: messagebox.showerror("Impossible",msg); return
        if not messagebox.askyesno("Confirmer","Annuler cette facture ? Les stocks seront restitués."): return
        try:
            self._db.annuler_vente(self._vente.id)
            for l in self._vente.lignes:
                arr_id=l.get("arrivage_id","")
                if arr_id:
                    try:
                        arrs=self._db.lister_arrivages(l["produit_id"]); found=False
                        for a in arrs:
                            if a.id==arr_id: self._db.modifier_arrivage_qte_restante(arr_id,a.quantite_restante+l["quantite"]); found=True; break
                        if not found:
                            ret=Arrivage(produit_id=l["produit_id"],quantite=l["quantite"],fournisseur="Retour",description=f"Retour {self._vente.id[:8]}")
                            self._db.ajouter_arrivage(ret)
                    except: pass
                self._db.recalculer_stock_produit(l["produit_id"])
                self._db.maj_description_produit_depuis_arrivages(l["produit_id"])
                self._db.ajouter_mouvement(MouvementStock(produit_id=l["produit_id"],produit_nom=l["produit_nom"],type_mvt="Annulation",quantite=l["quantite"],description=f"Annulation facture {self._vente.id[:8]}"))
            self._app.log_action("Annulation",f"Facture {self._vente.id[:8]} annulee",self._vente.id)
            messagebox.showinfo("OK","Facture annulée avec succès."); self._app.go_facture(self._vente.id)
        except Exception as e: messagebox.showerror("Erreur",str(e))



    def _pdf(self, vente):
        """Exporte une facture en PDF avec un design professionnel."""
        try:
            from fpdf import FPDF
            from datetime import datetime
            import os
            
            path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                initialfile=f"facture_{vente.id[:8]}.pdf"
            )
            if not path:
                return

            # Largeur utile du contenu = 190mm (marge 10 de chaque côté)
            W = 190

            class PDF(FPDF):
                def header(self):
                    self.set_font('Helvetica', 'B', 22)
                    self.set_text_color(37, 99, 235)
                    self.cell(0, 15, 'Pharmacie Colobane', ln=True, align='C')
                    self.set_draw_color(37, 99, 235)
                    self.set_line_width(0.5)
                    self.line(10, self.get_y() + 5, 10 + W, self.get_y() + 5)
                    self.ln(12)
            
            pdf = PDF()
            pdf.add_page()
            
            # En-tête de la facture
            pdf.set_font('Helvetica', 'B', 18)
            pdf.set_text_color(16, 185, 129)
            pdf.cell(0, 12, 'FACTURE / REÇU', ln=True, align='C')
            
            # Numéro de facture
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(37, 99, 235)
            pdf.cell(0, 8, f'N° {vente.id[:12].upper()}', ln=True, align='C')
            pdf.ln(6)

            # Cadre informations client — largeur W
            info_h = 25 + (7 if vente.structure_hospitaliere else 0)
            pdf.set_fill_color(226, 232, 240)
            pdf.set_draw_color(100, 116, 139)
            pdf.set_line_width(0.3)
            pdf.rect(10, pdf.get_y(), W, info_h, 'DF')
            
            pdf.set_xy(12, pdf.get_y() + 4)
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(50, 7, 'Client :', 0, 0, 'L')
            pdf.set_font('Helvetica', '', 11)
            pdf.cell(0, 7, vente.client_nom or 'Anonyme', ln=True)
            
            pdf.set_x(12)
            pdf.set_font('Helvetica', 'B', 11)
            pdf.cell(50, 7, 'Date :', 0, 0, 'L')
            pdf.set_font('Helvetica', '', 11)
            pdf.cell(0, 7, vente.date_vente[:19].replace('T', ' '), ln=True)
            
            if vente.structure_hospitaliere:
                pdf.set_x(12)
                pdf.set_font('Helvetica', 'B', 11)
                pdf.cell(50, 7, 'Structure :', 0, 0, 'L')
                pdf.set_font('Helvetica', '', 11)
                pdf.cell(0, 7, vente.structure_hospitaliere, ln=True)
            
            pdf.ln(10)
            
            # Tableau des produits — largeur totale = W (190mm)
            col_produit = W * 0.42  # ~80
            col_qte = W * 0.13     # ~25
            col_pu = W * 0.22      # ~42
            col_total = W * 0.23   # ~43
            
            # En-tête du tableau
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_fill_color(37, 99, 235)
            pdf.set_text_color(255, 255, 255)
            pdf.set_draw_color(37, 99, 235)
            pdf.set_line_width(0.2)
            
            pdf.cell(col_produit, 8, 'Produit', 1, 0, 'L', 1)
            pdf.cell(col_qte, 8, 'Qté', 1, 0, 'C', 1)
            pdf.cell(col_pu, 8, 'P.U. (FCFA)', 1, 0, 'R', 1)
            pdf.cell(col_total, 8, 'Sous-total (FCFA)', 1, 1, 'R', 1)
            
            # Lignes de produits
            pdf.set_text_color(30, 41, 59)
            pdf.set_font('Helvetica', '', 10)
            pdf.set_draw_color(200, 200, 200)
            
            lignes = vente.lignes if vente.lignes else [{
                "produit_nom": vente.produit_nom,
                "quantite": vente.quantite,
                "prix_unitaire": vente.prix_unitaire,
                "sous_total": vente.montant_total
            }]
            
            for i, l in enumerate(lignes):
                if i % 2 == 0:
                    pdf.set_fill_color(248, 250, 252)
                else:
                    pdf.set_fill_color(255, 255, 255)
                
                pdf.cell(col_produit, 7, str(l.get("produit_nom", ""))[:40], 'LR', 0, 'L', 1)
                pdf.cell(col_qte, 7, str(l.get("quantite", "")), 'LR', 0, 'C', 1)
                pdf.cell(col_pu, 7, f'{l.get("prix_unitaire", 0):,.0f}', 'LR', 0, 'R', 1)
                pdf.cell(col_total, 7, f'{l.get("sous_total", 0):,.0f}', 'LR', 1, 'R', 1)
            
            # Ligne de fermeture du tableau
            pdf.cell(W, 0, '', 'T')
            pdf.ln(8)
            
            # Total
            pdf.set_font('Helvetica', 'B', 16)
            pdf.set_text_color(16, 185, 129)
            pdf.cell(0, 12, f'TOTAL : {vente.montant_total:,.0f} FCFA', ln=True, align='R')
            pdf.ln(6)
            
            # Note sur l'annulation
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(0, 6, "Note : L'annulation de cette facture est possible dans un délai de 3 heures", ln=True, align='C')
            pdf.cell(0, 6, "suivant la vente. Passé ce délai, aucune annulation ne pourra être effectuée.", ln=True, align='C')
            pdf.ln(6)
            
            # Message de remerciement
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(37, 99, 235)
            pdf.cell(0, 8, 'Merci pour votre confiance !', ln=True, align='C')
            
            pdf.output(path)
            
            self._app.log_action("Export PDF", f"Facture {vente.id[:8]} exportée en PDF", vente.id)
            messagebox.showinfo("PDF", f"Facture exportée avec succès !\n\nFichier : {path}")
            
        except ImportError:
            messagebox.showerror("Erreur", "La bibliothèque fpdf n'est pas installée.\n\nInstallez-la avec : pip install fpdf")
        except Exception as e:
            messagebox.showerror("Erreur PDF", str(e))






class ChangerMdpFrame(ctk.CTkFrame, SidebarMixin):
    """Permet à tout utilisateur (ou administrateur) de changer son mot de passe."""
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="")
        main=ctk.CTkFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=22,pady=22); main.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(main,text="🔑 Changer le mot de passe",font=ctk.CTkFont(size=22,weight="bold"),text_color=C["pri"]).grid(row=0,column=0,sticky="w",pady=(0,16))
        box=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=14); box.grid(row=1,column=0,sticky="ew"); box.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(box,text="Mot de passe actuel",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=0,column=0,sticky="w",padx=24,pady=(18,2))
        _pf1,self._e_old=_make_pwd_entry(box,width=350,height=38,placeholder="Saisissez votre mot de passe actuel"); _pf1.grid(row=1,column=0,padx=24,pady=(0,10))
        ctk.CTkLabel(box,text="Nouveau mot de passe",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=2,column=0,sticky="w",padx=24,pady=(4,2))
        _pf2,self._e_new=_make_pwd_entry(box,width=350,height=38,placeholder="Nouveau mot de passe"); _pf2.grid(row=3,column=0,padx=24,pady=(0,10))
        ctk.CTkLabel(box,text="Confirmer le nouveau mot de passe",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=4,column=0,sticky="w",padx=24,pady=(4,2))
        _pf3,self._e_conf=_make_pwd_entry(box,width=350,height=38,placeholder="Confirmez le nouveau mot de passe"); _pf3.grid(row=5,column=0,padx=24,pady=(0,16))
        ctk.CTkButton(box,text="Mettre à jour",width=200,height=40,fg_color=C["pri"],hover_color=C["pri_h"],command=self._save).grid(row=6,column=0,pady=(0,20))
    def _save(self):
        old=self._e_old.get(); new=self._e_new.get(); conf=self._e_conf.get()
        if not old or not new or not conf: messagebox.showwarning("Requis","Veuillez remplir tous les champs."); return
        user=self._app.user
        if not user.verifier_mot_de_passe(old): messagebox.showerror("Erreur","Le mot de passe actuel est incorrect."); return
        if new!=conf: messagebox.showerror("Erreur","Les nouveaux mots de passe ne correspondent pas."); return
        ok,msg=Utilisateur.valider_mot_de_passe(new)
        if not ok: messagebox.showerror("Mot de passe invalide",msg); return
        try:
            user.password_hash=Utilisateur.hasher_mot_de_passe(new)
            self._db.modifier_utilisateur(user)
            self._app.log_action("Changement MDP",f"Mot de passe modifié par {user.username}",user.id)
            messagebox.showinfo("Succès","Votre mot de passe a été mis à jour avec succès !")
            self._app.go_dash()
        except Exception as e: messagebox.showerror("Erreur",str(e))

class AdminFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="admin")
        main=ctk.CTkFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=22,pady=22); main.grid_columnconfigure((0,1),weight=1)
        if not self._app.user or not self._app.user.is_admin:
            messagebox.showerror("Accès refusé","Seuls les administrateurs ont accès."); self._app.go_dash(); return
        ctk.CTkLabel(main,text="Administration",font=ctk.CTkFont(size=22,weight="bold"),text_color=C["admin"]).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,16))
        menus=[("Ajouter un produit","Créer un produit",master.go_ajout,C["sec"]),("Catégories","Gestion des catégories",master.go_admin_categories,"#8B5CF6"),("Arrivages","Lots et péremption",master.go_admin_arrivage,"#0891B2"),("Mouvements de stock","CI et pertes",master.go_admin_mouvements,C["pri"]),("Historique Actions","Journal d'audit",master.go_admin_historique,"#6D28D9"),("CA & Statistiques","CA par période",master.go_admin_ca,"#F59E0B"),("Utilisateurs","Comptes utilisateurs",master.go_admin_utilisateurs,"#0E7490"),("Exports et sauvegardes","CSV, PDF, base de données",master.go_admin_exports,"#0891B2")]
        for i,(t,d,cmd,col) in enumerate(menus):
            r,cc=divmod(i,2)
            card=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12,height=100); card.grid(row=r+1,column=cc,padx=8,pady=8,sticky="nsew"); card.grid_columnconfigure(0,weight=1)
            ctk.CTkLabel(card,text=t,font=ctk.CTkFont(size=14,weight="bold"),text_color=col).grid(row=0,column=0,padx=16,pady=(14,2),sticky="w")
            ctk.CTkLabel(card,text=d,font=ctk.CTkFont(size=10),text_color=C["txt2"]).grid(row=1,column=0,padx=16,pady=(0,6),sticky="w")
            ctk.CTkButton(card,text="Ouvrir",width=80,height=30,fg_color=col,command=cmd).grid(row=2,column=0,padx=16,pady=(0,14),sticky="w")

class AdminArrivageFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="adm_arr")
        main=ctk.CTkScrollableFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=20,pady=20); main.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(main,text="Enregistrer un arrivage",font=ctk.CTkFont(size=20,weight="bold"),text_color=C["admin"]).grid(row=0,column=0,sticky="w",pady=(0,12))
        box=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); box.grid(row=1,column=0,sticky="ew"); box.grid_columnconfigure((0,1),weight=1)
        try: prods=db.lister_produits()
        except: prods=[]
        self._prods={p.nom:p for p in prods}
        ctk.CTkLabel(box,text="Produit",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=0,column=0,sticky="w",padx=16,pady=(12,2))
        self._combo=ctk.CTkComboBox(box,values=[p.nom for p in prods] or ["-"],width=270,height=34); self._combo.grid(row=1,column=0,padx=16,sticky="w")
        ctk.CTkLabel(box,text="Quantité",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=0,column=1,sticky="w",padx=16,pady=(12,2))
        self._eq=ctk.CTkEntry(box,width=150,height=34,placeholder_text="Qte"); self._eq.grid(row=1,column=1,padx=16,sticky="w")
        ctk.CTkLabel(box,text="Date de péremption du lot",text_color=C["danger"],font=ctk.CTkFont(size=11,weight="bold")).grid(row=2,column=0,sticky="w",padx=16,pady=(10,2))
        self._eexp=ctk.CTkEntry(box,width=270,height=34,placeholder_text="AAAA-MM-JJ"); self._eexp.grid(row=3,column=0,padx=16,sticky="w")
        ctk.CTkLabel(box,text="Fournisseur",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=2,column=1,sticky="w",padx=16,pady=(10,2))
        self._ef=ctk.CTkEntry(box,width=270,height=34,placeholder_text="Fournisseur"); self._ef.grid(row=3,column=1,padx=16,sticky="w")
        ctk.CTkLabel(box,text="Description du lot",text_color=C["txt"],font=ctk.CTkFont(size=11)).grid(row=4,column=0,sticky="w",padx=16,pady=(10,2))
        self._ed=ctk.CTkEntry(box,width=560,height=34,placeholder_text="Details du lot"); self._ed.grid(row=5,column=0,columnspan=2,padx=16,sticky="w",pady=(0,10))
        ctk.CTkButton(box,text="Enregistrer l'arrivage",width=200,height=38,fg_color=C["sec"],hover_color=C["sec_h"],command=self._save).grid(row=6,column=0,columnspan=2,pady=14)
        ctk.CTkLabel(main,text="Derniers arrivages",font=ctk.CTkFont(size=14,weight="bold"),text_color=C["txt"]).grid(row=2,column=0,sticky="w",pady=(14,6))
        try: arrs=db.lister_arrivages()[:15]
        except: arrs=[]
        for i,a in enumerate(arrs):
            pnom=next((p.nom for p in prods if p.id==a.produit_id),a.produit_id[:8])
            prem=a.date_peremption or "N/A"
            ctk.CTkLabel(main,text=f"+{a.quantite}  {pnom}  exp:{prem}  ({a.fournisseur})  {a.date_arrivage[:16].replace('T',' ')}",font=ctk.CTkFont(size=10),text_color=C["txt"]).grid(row=3+i,column=0,sticky="w",padx=4)
        ctk.CTkButton(main,text="Retour à l'administration",width=120,height=34,fg_color=C["admin"],command=master.go_admin).grid(row=25,column=0,pady=14,sticky="w")
    def _save(self):
        pn=self._combo.get(); qs=self._eq.get().strip(); four=self._ef.get().strip()
        desc=self._ed.get().strip(); exp=self._eexp.get().strip()
        if not qs: messagebox.showwarning("Requis","La quantité est requise."); return
        if exp:
            ok,msg=Produit.valider_date_expiration(exp)
            if not ok: messagebox.showerror("Date",msg); return
        try: q=int(qs)
        except: messagebox.showerror("Erreur","Quantité invalide."); return
        p=self._prods.get(pn)
        if not p: messagebox.showerror("Erreur","Produit introuvable."); return
        try:
            a=Arrivage(produit_id=p.id,quantite=q,quantite_restante=q,fournisseur=four,description=desc,date_peremption=exp)
            self._db.ajouter_arrivage(a); p.incrementer_stock(q); self._db.modifier_produit(p)
            self._db.maj_description_produit_depuis_arrivages(p.id)
            self._db.ajouter_mouvement(MouvementStock(produit_id=p.id,produit_nom=p.nom,type_mvt="Entree",quantite=q,description=f"Arrivage {four} exp:{exp} {desc}"))
            self._app.log_action("Arrivage",f"+{q} {p.nom} exp:{exp} de {four}",p.id)
            messagebox.showinfo("OK",f"+{q} {p.nom} enregistré !"); self._app.show(AdminArrivageFrame)
        except Exception as e: messagebox.showerror("Erreur",str(e))



class PeremptionFrame(ctk.CTkFrame, SidebarMixin):
    """Alertes péremption accessible à tous (admin + gérant)."""
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="perm")
        main=ctk.CTkFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=18,pady=18); main.grid_columnconfigure(0,weight=1); main.grid_rowconfigure(3,weight=1)
        ctk.CTkLabel(main,text="Alertes de péremption (par lot)",font=ctk.CTkFont(size=20,weight="bold"),text_color=C["danger"]).grid(row=0,column=0,sticky="w",pady=(0,10))
        ft=ctk.CTkFrame(main,fg_color="transparent"); ft.grid(row=1,column=0,sticky="w",pady=(0,8))
        ctk.CTkLabel(ft,text="Délai (jours) :",text_color=C["txt"]).grid(row=0,column=0,padx=(0,6))
        self._jv=StringVar(value="30"); ctk.CTkEntry(ft,textvariable=self._jv,width=60,height=32).grid(row=0,column=1,padx=(0,8))
        ctk.CTkButton(ft,text="Filtrer",width=80,height=32,fg_color=C["pri"],command=self._load).grid(row=0,column=2)
        th=ctk.CTkFrame(main,fg_color=C["danger"],corner_radius=8,height=34); th.grid(row=2,column=0,sticky="ew"); th.grid_columnconfigure((0,1,2,3,4,5),weight=1)
        for i,h in enumerate(["Produit","Lot (exp.)","Jours restants","Stock lot","Fournisseur","Actions"]):
            ctk.CTkLabel(th,text=h,font=ctk.CTkFont(size=10,weight="bold"),text_color="white").grid(row=0,column=i,padx=6,pady=6)
        self._sc=ctk.CTkScrollableFrame(main,fg_color=C["bg"]); self._sc.grid(row=3,column=0,sticky="nsew"); self._sc.grid_columnconfigure((0,1,2,3,4,5),weight=1)
        self._load()
    def _load(self):
        for w in self._sc.winfo_children(): w.destroy()
        try: j=int(self._jv.get())
        except: j=30
        try: lots=self._db.arrivages_expires_ou_proches(j)
        except: lots=[]
        if not lots: ctk.CTkLabel(self._sc,text="Aucun lot concerné.",text_color=C["sec"]).grid(row=0,column=0,columnspan=6,pady=30); return
        for i,lot in enumerate(lots):
            jr=lot["jours_restants"]
            bg="#FEE2E2" if lot["est_perime"] else ("#FEF3C7" if jr<=7 else C["card"])
            rf=ctk.CTkFrame(self._sc,fg_color=bg,corner_radius=5); rf.grid(row=i,column=0,columnspan=6,sticky="ew",pady=1); rf.grid_columnconfigure((0,1,2,3,4,5),weight=1)
            jt=f"PÉRIMÉ ({abs(jr)} j)" if jr<0 else f"{jr} j"
            jc=C["danger"] if jr<=0 else (C["warn"] if jr<=7 else C["txt"])
            ctk.CTkLabel(rf,text=lot["produit_nom"],font=ctk.CTkFont(size=11),text_color=C["txt"]).grid(row=0,column=0,padx=8,pady=6)
            ctk.CTkLabel(rf,text=lot["date_peremption"],font=ctk.CTkFont(size=11),text_color=C["txt2"]).grid(row=0,column=1,padx=6)
            ctk.CTkLabel(rf,text=jt,font=ctk.CTkFont(size=11,weight="bold"),text_color=jc).grid(row=0,column=2,padx=6)
            ctk.CTkLabel(rf,text=str(lot["quantite_restante"]),font=ctk.CTkFont(size=11),text_color=C["txt"]).grid(row=0,column=3,padx=6)
            ctk.CTkLabel(rf,text=lot.get("fournisseur",""),font=ctk.CTkFont(size=10),text_color=C["txt2"]).grid(row=0,column=4,padx=6)
            if lot["est_perime"]:
                aid=lot.get("id",""); pid=lot.get("produit_id","")
                ctk.CTkButton(rf,text="Retirer le lot",width=85,height=24,font=ctk.CTkFont(size=9),fg_color=C["danger"],command=lambda _a=aid,_p=pid,_n=lot["produit_nom"],_q=lot["quantite_restante"]:self._suppr_lot(_a,_p,_n,_q)).grid(row=0,column=5,padx=4)
            else:
                ctk.CTkLabel(rf,text="-",text_color=C["txt2"],font=ctk.CTkFont(size=10)).grid(row=0,column=5,padx=4)
    def _suppr_lot(self,arrivage_id,produit_id,nom,qte):
        if not messagebox.askyesno("Confirmer",f"Retirer le lot périmé de {nom} ({qte} unités) ?\nCette action est irréversible."): return
        try:
            self._db.modifier_arrivage_qte_restante(arrivage_id,0)
            self._db.supprimer_lots_vides(produit_id)
            self._db.recalculer_stock_produit(produit_id)
            self._db.maj_description_produit_depuis_arrivages(produit_id)
            self._db.ajouter_mouvement(MouvementStock(produit_id=produit_id,produit_nom=nom,type_mvt="Perte",quantite=qte,description=f"Retrait lot périmé (suppression)"))
            self._app.log_action("Retrait périmé",f"Lot périmé {nom} x{qte} supprimé",arrivage_id)
            messagebox.showinfo("OK",f"Lot périmé retiré ({qte} unités retirées du stock)."); self._load()
        except Exception as e: messagebox.showerror("Erreur",str(e))

class AdminPeremptionFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="adm_per")
        main=ctk.CTkFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=18,pady=18); main.grid_columnconfigure(0,weight=1); main.grid_rowconfigure(3,weight=1)
        ctk.CTkLabel(main,text="Alertes de péremption",font=ctk.CTkFont(size=20,weight="bold"),text_color=C["danger"]).grid(row=0,column=0,sticky="w",pady=(0,10))
        ft=ctk.CTkFrame(main,fg_color="transparent"); ft.grid(row=1,column=0,sticky="w",pady=(0,8))
        ctk.CTkLabel(ft,text="Délai (jours) :",text_color=C["txt"]).grid(row=0,column=0,padx=(0,6))
        self._jv=StringVar(value="30"); ctk.CTkEntry(ft,textvariable=self._jv,width=60,height=32).grid(row=0,column=1,padx=(0,8))
        ctk.CTkButton(ft,text="Filtrer",width=80,height=32,fg_color=C["pri"],command=self._load).grid(row=0,column=2)
        th=ctk.CTkFrame(main,fg_color=C["danger"],corner_radius=8,height=34); th.grid(row=2,column=0,sticky="ew"); th.grid_columnconfigure((0,1,2,3),weight=1)
        for i,h in enumerate(["Nom","Expiration","Jours restants","Stock"]):
            ctk.CTkLabel(th,text=h,font=ctk.CTkFont(size=10,weight="bold"),text_color="white").grid(row=0,column=i,padx=6,pady=6)
        self._sc=ctk.CTkScrollableFrame(main,fg_color=C["bg"]); self._sc.grid(row=3,column=0,sticky="nsew"); self._sc.grid_columnconfigure((0,1,2,3),weight=1)
        self._load()
        ctk.CTkButton(main,text="Retour à l'administration",width=120,height=34,fg_color=C["admin"],command=master.go_admin).grid(row=4,column=0,pady=10,sticky="w")
    def _load(self):
        for w in self._sc.winfo_children(): w.destroy()
        try: j=int(self._jv.get())
        except: j=30
        try: prods=self._db.produits_expires_ou_proches(j)
        except: prods=[]
        if not prods: ctk.CTkLabel(self._sc,text="Aucun produit concerne.",text_color=C["sec"]).grid(row=0,column=0,columnspan=4,pady=30); return
        for i,p in enumerate(prods):
            bg="#FEE2E2" if p.est_expire() else ("#FEF3C7" if p.jours_avant_expiration()<=7 else C["card"])
            rf=ctk.CTkFrame(self._sc,fg_color=bg,corner_radius=5); rf.grid(row=i,column=0,columnspan=4,sticky="ew",pady=1); rf.grid_columnconfigure((0,1,2,3),weight=1)
            jr=p.jours_avant_expiration(); jt=f"PÉRIMÉ ({abs(jr)} j)" if jr<0 else f"{jr} j"
            jc=C["danger"] if jr<=0 else (C["warn"] if jr<=7 else C["txt"])
            ctk.CTkLabel(rf,text=p.nom,font=ctk.CTkFont(size=11),text_color=C["txt"]).grid(row=0,column=0,padx=8,pady=6)
            ctk.CTkLabel(rf,text=p.date_expiration,font=ctk.CTkFont(size=11),text_color=C["txt2"]).grid(row=0,column=1,padx=6)
            ctk.CTkLabel(rf,text=jt,font=ctk.CTkFont(size=11,weight="bold"),text_color=jc).grid(row=0,column=2,padx=6)
            ctk.CTkLabel(rf,text=str(p.quantite),font=ctk.CTkFont(size=11),text_color=C["txt"]).grid(row=0,column=3,padx=6)

class AdminMouvementsFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="adm_mvt")
        main=ctk.CTkScrollableFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=18,pady=18); main.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(main,text="Mouvements de stock",font=ctk.CTkFont(size=20,weight="bold"),text_color=C["pri"]).grid(row=0,column=0,sticky="w",pady=(0,6))
        box=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); box.grid(row=1,column=0,sticky="ew",pady=(0,10)); box.grid_columnconfigure((0,1),weight=1)
        ctk.CTkLabel(box,text="Enregistrer CI / perte (choix du lot)",font=ctk.CTkFont(size=12,weight="bold"),text_color=C["txt"]).grid(row=0,column=0,columnspan=2,sticky="w",padx=14,pady=(10,6))
        try: prods=db.lister_produits()
        except: prods=[]
        self._prods={p.nom:p for p in prods}
        ctk.CTkLabel(box,text="Produit :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=1,column=0,padx=14,sticky="w",pady=(4,0))
        self._combo=ctk.CTkComboBox(box,values=[p.nom for p in prods] or ["-"],width=220,height=32,command=self._on_prod); self._combo.grid(row=2,column=0,padx=14,sticky="w")
        ctk.CTkLabel(box,text="Lot (y compris périmés) :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=1,column=1,padx=4,sticky="w",pady=(4,0))
        self._clot=ctk.CTkComboBox(box,values=["-"],width=280,height=32); self._clot.grid(row=2,column=1,padx=4,sticky="w")
        self._lots_data={}
        ctk.CTkLabel(box,text="Type :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=3,column=0,padx=14,sticky="w",pady=(6,0))
        self._tc=ctk.CTkComboBox(box,values=["Consommation interne","Perte"],width=180,height=32); self._tc.grid(row=4,column=0,padx=14,sticky="w")
        ctk.CTkLabel(box,text="Quantité :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=3,column=1,padx=4,sticky="w",pady=(6,0))
        self._eq=ctk.CTkEntry(box,width=80,height=32,placeholder_text="Qte"); self._eq.grid(row=4,column=1,padx=4,sticky="w")
        ctk.CTkLabel(box,text="Description (obligatoire) :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=5,column=0,padx=14,sticky="w",pady=(6,0))
        self._ed=ctk.CTkEntry(box,width=500,height=32,placeholder_text="Description du mouvement"); self._ed.grid(row=6,column=0,columnspan=2,padx=14,pady=(0,10),sticky="w")
        ctk.CTkButton(box,text="Enregistrer le mouvement",width=160,height=34,fg_color=C["warn"],command=self._save).grid(row=7,column=0,columnspan=2,padx=14,pady=(0,14))
        self._on_prod(self._combo.get() if prods else "")
        ctk.CTkLabel(main,text="Historique des mouvements",font=ctk.CTkFont(size=14,weight="bold"),text_color=C["txt"]).grid(row=2,column=0,sticky="w",pady=(10,6))
        try: mvts=db.lister_mouvements()[:50]
        except: mvts=[]
        for i,m in enumerate(mvts):
            tc=C["sec"] if m.type_mvt=="Entree" else (C["danger"] if m.type_mvt in ("Perte","Vente","Annulation") else C["warn"])
            dt=m.date_mvt[:16].replace("T"," ")
            ctk.CTkLabel(main,text=f"[{m.type_mvt}] {m.produit_nom} x{m.quantite} - {m.description} ({dt})",font=ctk.CTkFont(size=10),text_color=tc).grid(row=3+i,column=0,sticky="w",padx=4,pady=1)
        ctk.CTkButton(main,text="Retour à l'administration",width=120,height=34,fg_color=C["admin"],command=master.go_admin).grid(row=60,column=0,pady=14,sticky="w")
    def _on_prod(self,pn):
        """Charger TOUS les lots du produit (y compris périmés) pour CI/perte."""
        self._lots_data={}
        p=self._prods.get(pn)
        if not p: self._clot.configure(values=["-"]); self._clot.set("-"); return
        try: arrs=self._db.lister_arrivages(p.id)
        except: arrs=[]
        lots_avec_stock=[a for a in arrs if a.quantite_restante>0]
        if not lots_avec_stock: self._clot.configure(values=["Aucun lot disponible"]); self._clot.set("Aucun lot disponible"); return
        vals=[]
        for a in lots_avec_stock:
            exp=a.date_peremption or "sans exp."
            perime=" [PÉRIMÉ]" if a.est_perime() else ""
            lbl=f"Lot {a.date_arrivage[:10]} | rest:{a.quantite_restante} | exp:{exp}{perime}"
            vals.append(lbl); self._lots_data[lbl]=a
        self._clot.configure(values=vals); self._clot.set(vals[0])
    def _save(self):
        pn=self._combo.get(); qs=self._eq.get().strip(); tp=self._tc.get(); desc=self._ed.get().strip(); lot_key=self._clot.get()
        if not desc: messagebox.showerror("Requis","La description est obligatoire pour tout mouvement."); return
        if not qs: messagebox.showwarning("Requis","La quantité est requise."); return
        p=self._prods.get(pn)
        if not p: messagebox.showerror("Erreur","Produit introuvable."); return
        arr=self._lots_data.get(lot_key)
        if not arr: messagebox.showerror("Erreur","Veuillez sélectionner un lot valide."); return
        try:
            q=int(qs)
            if q<=0: raise ValueError("La quantité doit être supérieure à 0.")
            if q>arr.quantite_restante: messagebox.showerror("Stock","Stock insuffisant dans ce lot."); return
            self._db.modifier_arrivage_qte_restante(arr.id, arr.quantite_restante - q)
            self._db.supprimer_lots_vides(p.id)
            self._db.recalculer_stock_produit(p.id)
            self._db.maj_description_produit_depuis_arrivages(p.id)
            self._db.ajouter_mouvement(MouvementStock(produit_id=p.id,produit_nom=p.nom,type_mvt=tp,quantite=q,description=f"{desc} [lot:{arr.id[:8]} exp:{arr.date_peremption or 'N/A'}]"))
            self._app.log_action(tp,f"{tp} {p.nom} x{q} lot:{arr.id[:8]} - {desc}",p.id)
            messagebox.showinfo("OK","Mouvement enregistré ! Stock du lot mis à jour."); self._app.show(AdminMouvementsFrame)
        except ValueError as e: messagebox.showerror("Saisie",str(e))
        except Exception as e: messagebox.showerror("Erreur",str(e))


class AdminHistoriqueFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="adm_hist")
        main=ctk.CTkFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=18,pady=18); main.grid_columnconfigure(0,weight=1); main.grid_rowconfigure(3,weight=1)
        ctk.CTkLabel(main,text="Historique des actions (audit)",font=ctk.CTkFont(size=20,weight="bold"),text_color=C["admin"]).grid(row=0,column=0,sticky="w",pady=(0,10))
        ft=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=10); ft.grid(row=1,column=0,sticky="ew",pady=(0,6))
        ctk.CTkLabel(ft,text="Recherche :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=0,column=0,padx=(12,4),pady=6)
        self._sv=StringVar(); ctk.CTkEntry(ft,textvariable=self._sv,width=160,height=30,placeholder_text="Description, utilisateur...").grid(row=0,column=1,padx=2)
        ctk.CTkLabel(ft,text="Type :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=0,column=2,padx=(8,4))
        self._ft=ctk.CTkComboBox(ft,values=["Tous","Ajout","Modification","Suppression","Vente","Arrivage","Export"],width=130,height=30); self._ft.grid(row=0,column=3,padx=2)
        ctk.CTkButton(ft,text="Filtrer",width=70,height=30,fg_color=C["pri"],command=self._load).grid(row=0,column=4,padx=(8,12))
        th=ctk.CTkFrame(main,fg_color=C["admin"],corner_radius=8,height=34); th.grid(row=2,column=0,sticky="ew"); th.grid_columnconfigure((0,1,2,3,4),weight=1)
        for i,h in enumerate(["Date & Heure","Utilisateur","Action","Description","Cible"]):
            ctk.CTkLabel(th,text=h,font=ctk.CTkFont(size=10,weight="bold"),text_color="white").grid(row=0,column=i,padx=5,pady=6)
        self._sc=ctk.CTkScrollableFrame(main,fg_color=C["bg"]); self._sc.grid(row=3,column=0,sticky="nsew"); self._sc.grid_columnconfigure((0,1,2,3,4),weight=1)
        self._load()
        ctk.CTkButton(main,text="Retour à l'administration",width=120,height=34,fg_color=C["admin"],command=master.go_admin).grid(row=4,column=0,pady=10,sticky="w")
    def _load(self):
        for w in self._sc.winfo_children(): w.destroy()
        terme=self._sv.get().strip(); at=self._ft.get()
        action_type="" if at=="Tous" else at
        try: actions=self._db.filtrer_actions(terme=terme,action_type=action_type)
        except: actions=[]
        if not actions: ctk.CTkLabel(self._sc,text="Aucune action enregistrée.",text_color=C["txt2"]).grid(row=0,column=0,columnspan=5,pady=30); return
        for i,a in enumerate(actions):
            bg=C["card"] if i%2==0 else "#F1F5F9"
            rf=ctk.CTkFrame(self._sc,fg_color=bg,corner_radius=4); rf.grid(row=i,column=0,columnspan=5,sticky="ew",pady=1); rf.grid_columnconfigure((0,1,2,3,4),weight=1)
            dt=a.date_action[:19].replace("T"," ")
            full_desc=a.description
            short_desc=a.description[:50]+("..." if len(a.description)>50 else "")
            for j,val in enumerate([dt,a.utilisateur,a.action,short_desc,a.cible[:12]]):
                if j==3 and len(full_desc)>50:
                    dl=ctk.CTkLabel(rf,text=val,font=ctk.CTkFont(size=9),text_color=C["pri"],cursor="hand2")
                    dl.grid(row=0,column=j,padx=4,pady=4)
                    dl.bind("<Button-1>",lambda e,fd=full_desc:messagebox.showinfo("Description complète",fd))
                else:
                    ctk.CTkLabel(rf,text=val,font=ctk.CTkFont(size=9),text_color=C["txt"]).grid(row=0,column=j,padx=4,pady=4)

class AdminExportsFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="adm_exp")
        main=ctk.CTkFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=22,pady=22); main.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(main,text="Exports et sauvegardes",font=ctk.CTkFont(size=20,weight="bold"),text_color=C["pri"]).grid(row=0,column=0,sticky="w",pady=(0,16))
        acts=[("Exporter les produits (CSV)","Fichier CSV des produits",self._epc,C["sec"]),("Exporter les ventes (CSV)","Historique des ventes en CSV",self._evc,C["sec"]),("Sauvegarder la base","Copie locale de la base de données",self._bkp,"#0891B2"),("Sauvegarder sur Drive","Envoi vers Google Drive (connexion requise)",self._bkp_drive,"#7C3AED")]
        for i,(t,d,cmd,col) in enumerate(acts):
            f=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=10); f.grid(row=i+1,column=0,sticky="ew",padx=4,pady=5); f.grid_columnconfigure(0,weight=1)
            ctk.CTkLabel(f,text=t,font=ctk.CTkFont(size=13,weight="bold"),text_color=col).grid(row=0,column=0,padx=16,pady=(10,2),sticky="w")
            ctk.CTkLabel(f,text=d,font=ctk.CTkFont(size=10),text_color=C["txt2"]).grid(row=1,column=0,padx=16,pady=(0,10),sticky="w")
            ctk.CTkButton(f,text="Lancer",width=90,height=30,fg_color=col,command=cmd).grid(row=0,column=1,rowspan=2,padx=16)
        ctk.CTkButton(main,text="Retour à l'administration",width=120,height=34,fg_color=C["admin"],command=master.go_admin).grid(row=10,column=0,pady=14,sticky="w")
    def _epc(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")],initialfile="produits.csv")
        if path:
            try: self._db.exporter_csv(path); self._app.log_action("Export","Export CSV produits"); messagebox.showinfo("OK",f"Exporte: {path}")
            except Exception as e: messagebox.showerror("Erreur",str(e))
    def _evc(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")],initialfile="ventes.csv")
        if path:
            try: self._db.exporter_ventes_csv(path); self._app.log_action("Export","Export CSV ventes"); messagebox.showinfo("OK",f"Exporte: {path}")
            except Exception as e: messagebox.showerror("Erreur",str(e))
    def _bkp(self):
        dest=filedialog.askdirectory(title="Choisir le dossier de sauvegarde")
        if dest:
            try: bk=self._db.sauvegarder_base(dest); self._app.log_action("Backup",f"Sauvegarde DB vers {bk}"); messagebox.showinfo("OK",f"Sauvegarde créée :\n{bk}")
            except Exception as e: messagebox.showerror("Erreur",str(e))
    def _bkp_drive(self):
        try:
            import subprocess, shutil, tempfile
            # Étape 1 : sauvegarde locale temporaire
            tmp = tempfile.mkdtemp()
            bk = self._db.sauvegarder_base(tmp)
            bk_name = os.path.basename(bk)
            # Étape 2 : tentative upload via Google Drive API (PyDrive2)
            try:
                from pydrive2.auth import GoogleAuth
                from pydrive2.drive import GoogleDrive
                gauth = GoogleAuth()
                gauth.LocalWebserverAuth()
                drive = GoogleDrive(gauth)
                f = drive.CreateFile({"title": bk_name, "parents": [{"id": "root"}]})
                f.SetContentFile(bk)
                f.Upload()
                self._app.log_action("Backup Drive", f"Sauvegarde envoyée sur Google Drive : {bk_name}")
                messagebox.showinfo("Succès", f"Base de données sauvegardée sur Google Drive !\n\nFichier : {bk_name}")
                return
            except ImportError:
                pass
            except Exception as e_drive:
                messagebox.showwarning("Google Drive API", f"Échec de l'envoi automatique :\n{e_drive}\n\nVeuillez sélectionner un dossier synchronisé manuellement.")
            # Fallback : sélection manuelle d'un dossier cloud synchronisé
            messagebox.showinfo("Sauvegarde cloud",
                "Pour sauvegarder sur Google Drive :\n\n"
                "1. Installez Google Drive pour bureau\n"
                "   (https://www.google.com/drive/download/)\n\n"
                "2. Sélectionnez le dossier « Mon Drive » synchronisé\n\n"
                "Ou installez PyDrive2 :\n   pip install pydrive2")
            dest = filedialog.askdirectory(title="Sélectionner le dossier Google Drive synchronisé")
            if dest:
                import shutil as sh
                final = os.path.join(dest, bk_name)
                sh.copy2(bk, final)
                self._app.log_action("Backup Drive", f"Sauvegarde copiée vers {final}")
                messagebox.showinfo("Succès", f"Base sauvegardée dans :\n{final}\n\nElle sera synchronisée automatiquement si le dossier est lié à Google Drive.")
        except Exception as e: messagebox.showerror("Erreur", str(e))

class AdminUtilisateursFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="adm_usr")
        main=ctk.CTkScrollableFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=18,pady=18); main.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(main,text="Comptes utilisateurs",font=ctk.CTkFont(size=20,weight="bold"),text_color=C["admin"]).grid(row=0,column=0,sticky="w",pady=(0,10))
        th=ctk.CTkFrame(main,fg_color=C["admin"],corner_radius=8,height=34); th.grid(row=1,column=0,sticky="ew"); th.grid_columnconfigure((0,1,2,3),weight=1)
        for i,h in enumerate(["Utilisateur","E-mail","Rôle","Actions"]):
            ctk.CTkLabel(th,text=h,font=ctk.CTkFont(size=10,weight="bold"),text_color="white").grid(row=0,column=i,padx=6,pady=6)
        try: users=db.lister_utilisateurs()
        except: users=[]
        for i,u in enumerate(users):
            bg=C["card"] if i%2==0 else "#F1F5F9"
            rf=ctk.CTkFrame(main,fg_color=bg,corner_radius=4); rf.grid(row=i+2,column=0,sticky="ew",pady=1); rf.grid_columnconfigure((0,1,2,3),weight=1)
            ctk.CTkLabel(rf,text=u.username,font=ctk.CTkFont(size=11),text_color=C["txt"]).grid(row=0,column=0,padx=6,pady=5)
            ctk.CTkLabel(rf,text=u.email,font=ctk.CTkFont(size=10),text_color=C["txt2"]).grid(row=0,column=1,padx=6,pady=5)
            role="Administrateur" if u.is_admin else "Utilisateur"
            ctk.CTkLabel(rf,text=role,font=ctk.CTkFont(size=10,weight="bold"),text_color=C["admin"] if u.is_admin else C["txt"]).grid(row=0,column=2,padx=6,pady=5)
            af=ctk.CTkFrame(rf,fg_color="transparent"); af.grid(row=0,column=3,padx=4)
            uid=u.id; uname=u.username
            ctk.CTkButton(af,text="Réinitialiser MDP",width=105,height=24,font=ctk.CTkFont(size=9),fg_color=C["warn"],command=lambda _id=uid,_n=uname:self._reset_pwd(_id,_n)).grid(row=0,column=0,padx=2) if not u.is_admin else None
            if not u.is_admin:
                ctk.CTkButton(af,text="Supprimer",width=75,height=24,font=ctk.CTkFont(size=9),fg_color=C["danger"],command=lambda _id=uid,_n=uname:self._del_user(_id,_n)).grid(row=0,column=1,padx=2)
        ctk.CTkButton(main,text="Retour à l'administration",width=140,height=34,fg_color=C["admin"],command=master.go_admin).grid(row=len(users)+3,column=0,pady=10,sticky="w")
    def _reset_pwd(self,uid,uname):
        if not messagebox.askyesno("Confirmer",f"Réinitialiser le mot de passe de « {uname} » ?\nUn mot de passe temporaire sera généré."): return
        try:
            users=self._db.lister_utilisateurs()
            user=next((u for u in users if u.id==uid),None)
            if not user: return
            temp_pwd=Utilisateur.generer_mdp_temporaire()
            user.password_hash=Utilisateur.hasher_mot_de_passe(temp_pwd)
            user.must_change_password=True
            self._db.modifier_utilisateur(user)
            self._app.log_action("Réinitialisation MDP",f"MDP réinitialisé pour {uname}",uid)
            messagebox.showinfo("Mot de passe temporaire",f"Nouveau mot de passe temporaire pour « {uname} » :\n\n{temp_pwd}\n\nL'utilisateur devra le changer à sa prochaine connexion.\nNotez-le et transmettez-le de manière sécurisée.")
        except Exception as e: messagebox.showerror("Erreur",str(e))
    def _del_user(self,uid,uname):
        if not messagebox.askyesno("Confirmer",f"Supprimer définitivement le compte « {uname} » ?\nCette action est irréversible."): return
        try:
            self._db.supprimer_utilisateur(uid)
            self._app.log_action("Suppression utilisateur",f"Compte « {uname} » supprimé",uid)
            messagebox.showinfo("Succès",f"Le compte « {uname} » a été supprimé.")
            self._app.go_admin_utilisateurs()
        except Exception as e: messagebox.showerror("Erreur",str(e))

class AdminCAFrame(ctk.CTkFrame, SidebarMixin):
    def __init__(self,master,db,**kw):
        super().__init__(master,fg_color=C["bg"]); self._app,self._db=master,db
        self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self._sidebar(self,master,active="adm_ca")
        main=ctk.CTkScrollableFrame(self,fg_color=C["bg"]); main.grid(row=0,column=1,sticky="nsew",padx=18,pady=18); main.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(main,text="Chiffre d'affaires et statistiques",font=ctk.CTkFont(size=20,weight="bold"),text_color=C["admin"]).grid(row=0,column=0,sticky="w",pady=(0,6))
        # R6+R7 : Note importante sur la logique des statistiques
        note_frame=ctk.CTkFrame(main,fg_color="#FEF3C7",corner_radius=8); note_frame.grid(row=1,column=0,sticky="ew",pady=(0,10)); note_frame.grid_columnconfigure(0,weight=1)
        note_txt=("⚠️ Note importante :\n"
                  "• Lorsque vous choisissez une plage de dates (du jour n au jour m), les statistiques affichées couvrent "
                  "les ventes du jour n au jour m−1. En effet, la réinitialisation du CA du jour m−1 s'effectue à m à 05h00. "
                  "Seules les ventes des jours dont le CA a déjà été réinitialisé sont comptabilisées.\n"
                  "• Les ventes prises en compte dans les statistiques sont uniquement celles déjà enregistrées "
                  "dans la base de données et dont le chiffre d'affaires a été réinitialisé (cycle quotidien à 05h00).")
        ctk.CTkLabel(note_frame,text=note_txt,text_color="#92400E",font=ctk.CTkFont(size=10),wraplength=700,justify="left").grid(row=0,column=0,padx=12,pady=8,sticky="w")
        today=date.today().isoformat()
        try: ca_jour=db.ca_journalier(today)
        except: ca_jour=0
        ctk.CTkLabel(main,text=f"CA du jour (depuis 5h00): {ca_jour:,.0f} FCFA",font=ctk.CTkFont(size=16,weight="bold"),text_color=C["sec"]).grid(row=2,column=0,sticky="w",pady=(0,12))
        box=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); box.grid(row=3,column=0,sticky="ew",pady=(0,10)); box.grid_columnconfigure((0,1,2,3),weight=1)
        ctk.CTkLabel(box,text="Date de début (AAAA-MM-JJ) :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=0,column=0,padx=12,pady=8,sticky="w")
        d30=date.today()-timedelta(days=30)
        self._ed1=ctk.CTkEntry(box,width=130,height=32); self._ed1.insert(0,d30.isoformat()); self._ed1.grid(row=0,column=1,padx=4,sticky="w")
        ctk.CTkLabel(box,text="Date de fin :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=0,column=2,padx=4,sticky="w")
        self._ed2=ctk.CTkEntry(box,width=130,height=32); self._ed2.insert(0,today); self._ed2.grid(row=0,column=3,padx=4,sticky="w")
        ctk.CTkLabel(box,text="Granularité :",text_color=C["txt"],font=ctk.CTkFont(size=10)).grid(row=1,column=0,padx=12,pady=(0,8),sticky="w")
        self._gran=ctk.CTkComboBox(box,values=["Jour","Semaine","Mois"],width=120,height=32); self._gran.grid(row=1,column=1,padx=4,pady=(0,8),sticky="w")
        ctk.CTkButton(box,text="Calculer",width=100,height=32,fg_color=C["pri"],command=self._calc).grid(row=1,column=2,padx=4,pady=(0,8))
        self._result_lbl=ctk.CTkLabel(main,text="",font=ctk.CTkFont(size=14,weight="bold"),text_color=C["sec"]); self._result_lbl.grid(row=4,column=0,sticky="w",pady=6)
        self._chart_frame=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); self._chart_frame.grid(row=5,column=0,sticky="ew",pady=8)
        # Section ventes par produit + categorie
        ctk.CTkLabel(main,text="Ventes par produit (quantités et valeurs)",font=ctk.CTkFont(size=14,weight="bold"),text_color=C["txt"]).grid(row=6,column=0,sticky="w",pady=(12,4))
        self._prod_frame=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); self._prod_frame.grid(row=7,column=0,sticky="ew",pady=4); self._prod_frame.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(main,text="Agrégation par catégorie",font=ctk.CTkFont(size=14,weight="bold"),text_color=C["txt"]).grid(row=8,column=0,sticky="w",pady=(12,4))
        self._cat_frame=ctk.CTkFrame(main,fg_color=C["card"],corner_radius=12); self._cat_frame.grid(row=9,column=0,sticky="ew",pady=4); self._cat_frame.grid_columnconfigure(0,weight=1)
        ctk.CTkButton(main,text="Retour à l'administration",width=120,height=34,fg_color=C["admin"],command=master.go_admin).grid(row=10,column=0,pady=10,sticky="w")
    def _calc(self):
        d1=self._ed1.get().strip(); d2=self._ed2.get().strip(); gran=self._gran.get()
        try:
            ca_total=self._db.ca_par_periode(d1,d2)
            self._result_lbl.configure(text=f"CA total du {d1} au {d2}: {ca_total:,.0f} FCFA")
            if gran=="Jour":
                data=self._db.ventes_par_jour(d1,d2)
                labels=[d["jour"] for d in data]; values=[d["ca"] for d in data]
            elif gran=="Semaine":
                data=self._db.ventes_par_semaine(d1,d2)
                labels=[d["semaine"] for d in data]; values=[d["ca"] for d in data]
            else:
                data=self._db.ventes_par_mois(d1,d2)
                labels=[d["mois"] for d in data]; values=[d["ca"] for d in data]
            for w in self._chart_frame.winfo_children(): w.destroy()
            if data:
                try:
                    import matplotlib; matplotlib.use("Agg")
                    import matplotlib.pyplot as plt
                    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
                    fig,ax=plt.subplots(figsize=(7,2.5),dpi=100); fig.patch.set_facecolor("#F8FAFC")
                    ax.bar(labels,values,color="#2563EB",alpha=0.8)
                    ax.set_ylabel("FCFA",fontsize=8); ax.set_title(f"Évolution du CA par {gran.lower()}",fontsize=10,fontweight="bold")
                    ax.tick_params(axis="x",labelsize=5 if gran=="Jour" else 7,rotation=45); ax.tick_params(axis="y",labelsize=8)
                    ax.set_facecolor("#F8FAFC"); fig.tight_layout()
                    canvas=FigureCanvasTkAgg(fig,master=self._chart_frame); canvas.draw(); canvas.get_tk_widget().pack(padx=8,pady=8)
                except: pass
            # Ventes par produit
            self._show_ventes_produit(d1,d2)
            self._show_ventes_categorie(d1,d2)
        except Exception as e: messagebox.showerror("Erreur",str(e))
    def _show_ventes_produit(self,d1,d2):
        for w in self._prod_frame.winfo_children(): w.destroy()
        try: data=self._db.ventes_par_produit(d1,d2)
        except: data=[]
        if not data: ctk.CTkLabel(self._prod_frame,text="Aucune vente sur cette période.",text_color=C["txt2"]).grid(padx=16,pady=10); return
        hf=ctk.CTkFrame(self._prod_frame,fg_color=C["pri"],corner_radius=6,height=28); hf.grid(row=0,column=0,sticky="ew",padx=12,pady=(8,2)); hf.grid_columnconfigure((0,1,2),weight=1)
        for j,h in enumerate(["Produit","Quantité vendue","CA (FCFA)"]): ctk.CTkLabel(hf,text=h,font=ctk.CTkFont(size=10,weight="bold"),text_color="white").grid(row=0,column=j,padx=6,pady=4)
        for i,d in enumerate(data):
            bg=C["card"] if i%2==0 else "#F1F5F9"
            rf=ctk.CTkFrame(self._prod_frame,fg_color=bg,corner_radius=3); rf.grid(row=i+1,column=0,sticky="ew",padx=12,pady=1); rf.grid_columnconfigure((0,1,2),weight=1)
            ctk.CTkLabel(rf,text=d["produit_nom"],font=ctk.CTkFont(size=10),text_color=C["txt"]).grid(row=0,column=0,padx=6,pady=3)
            ctk.CTkLabel(rf,text=str(d["quantite_totale"]),font=ctk.CTkFont(size=10,weight="bold"),text_color=C["txt"]).grid(row=0,column=1,padx=6,pady=3)
            ctk.CTkLabel(rf,text=f'{d["ca"]:,.0f}',font=ctk.CTkFont(size=10,weight="bold"),text_color=C["sec"]).grid(row=0,column=2,padx=6,pady=3)
        ctk.CTkFrame(self._prod_frame,fg_color="transparent",height=8).grid(row=len(data)+1,column=0)
    def _show_ventes_categorie(self,d1,d2):
        for w in self._cat_frame.winfo_children(): w.destroy()
        try: data=self._db.ventes_par_categorie(d1,d2)
        except: data=[]
        if not data: ctk.CTkLabel(self._cat_frame,text="Aucune vente sur cette période.",text_color=C["txt2"]).grid(padx=16,pady=10); return
        hf=ctk.CTkFrame(self._cat_frame,fg_color="#8B5CF6",corner_radius=6,height=28); hf.grid(row=0,column=0,sticky="ew",padx=12,pady=(8,2)); hf.grid_columnconfigure((0,1,2),weight=1)
        for j,h in enumerate(["Catégorie","Quantité vendue","CA (FCFA)"]): ctk.CTkLabel(hf,text=h,font=ctk.CTkFont(size=10,weight="bold"),text_color="white").grid(row=0,column=j,padx=6,pady=4)
        for i,d in enumerate(data):
            bg=C["card"] if i%2==0 else "#F1F5F9"
            rf=ctk.CTkFrame(self._cat_frame,fg_color=bg,corner_radius=3); rf.grid(row=i+1,column=0,sticky="ew",padx=12,pady=1); rf.grid_columnconfigure((0,1,2),weight=1)
            ctk.CTkLabel(rf,text=d["categorie_nom"],font=ctk.CTkFont(size=10),text_color=C["txt"]).grid(row=0,column=0,padx=6,pady=3)
            ctk.CTkLabel(rf,text=str(d["quantite_totale"]),font=ctk.CTkFont(size=10,weight="bold"),text_color=C["txt"]).grid(row=0,column=1,padx=6,pady=3)
            ctk.CTkLabel(rf,text=f'{d["ca"]:,.0f}',font=ctk.CTkFont(size=10,weight="bold"),text_color=C["sec"]).grid(row=0,column=2,padx=6,pady=3)
        ctk.CTkFrame(self._cat_frame,fg_color="transparent",height=8).grid(row=len(data)+1,column=0)
