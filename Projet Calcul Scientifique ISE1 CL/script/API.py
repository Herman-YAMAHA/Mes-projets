import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ============================================================
# CONFIGURATION & STYLE
# ============================================================
UI = {
    'sidebar': '#1E293B',
    'accent': '#10B981', 
    'real': '#64748B',    
    'danger': '#EF4444',
    'bg_light': '#F8FAFC',
    'button_alt': '#334155'
}

CATS_MAP = {
    'Effectif total': 'Total',
    'Mâles matures (M)': 'M',
    'Femelles matures non gestantes (F)': 'F',
    'Femelles gestantes (FP)': 'FP',
    'Jeunes mâles (JM)': 'JM',
    'Jeunes femelles (JF)': 'JF'
}

PARAMS_DEF = {
    'gm': 0.25, 'gf': 0.90, 'mu_M': 0.21, 'tau_M': 0.01,
    'tau_F': 0.001, 'mu_F': 0.11, 'delta_M': 0.20, 'delta_F': 0.10,
    'd': 1.15, 'mu_Fp': 0.15, 'lambda_m': 0.432, 'lambda_f': 0.598,
    'mu_m': 0.171, 'mu_f': 0.134, 'k': 60000.0,
}

# ============================================================
# MOTEUR RK4
# ============================================================
def systeme_edo(t, Y, p):
    M, F, Fp, JM, JF = [max(v, 0.0) for v in Y]
    appariement = (F * M / (M + p['k'])) if (M + p['k']) > 0 else 0
    dM = p['gm']*JM - (p['mu_M'] + p['tau_M'] + p['delta_M'])*M
    dF = p['gf']*JF - appariement - (p['mu_F'] + p['tau_F'] + p['delta_F'])*F + p['d']*Fp
    dFp = appariement - (p['d'] + p['mu_Fp'])*Fp
    dJM = p['lambda_m']*Fp - (p['gm'] + p['mu_m'])*JM
    dJF = p['lambda_f']*Fp - (p['gf'] + p['mu_f'])*JF
    return np.array([dM, dF, dFp, dJM, dJF])

def resoudre_rk4(Y0, p, t0=0, tf=24, h=0.01):
    t_vals, y_vals = [t0], [Y0]
    t, y = t0, Y0
    while t < tf:
        k1 = systeme_edo(t, y, p)
        k2 = systeme_edo(t + h/2, y + h/2*k1, p)
        k3 = systeme_edo(t + h/2, y + h/2*k2, p)
        k4 = systeme_edo(t + h, y + h*k3, p)
        y = y + (h/6)*(k1 + 2*k2 + 2*k3 + k4)
        t += h
        t_vals.append(t)
        y_vals.append(y.copy())
    return np.array(t_vals), np.array(y_vals)

# ============================================================
# APPLICATION
# ============================================================
class SimulateurOvinV9(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulateur de Cheptel Ovin (Sénégal)")
        self.geometry("1550x950")
        
        try:
            self.df_reel = pd.read_excel(chemin_data / 'base_ovins_nettoyee.xlsx')
        except:
            messagebox.showerror("Erreur", "Fichier data/base_ovins_nettoyee.xlsx introuvable.")
            self.df_reel = None

        self._build_ui()
        self._simuler()

    def _build_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=UI['sidebar'], width=280)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="CONTRÔLE", font=('Arial', 14, 'bold'), bg=UI['sidebar'], fg='white', pady=20).pack()
        
        tk.Label(self.sidebar, text="Taux d'abattage (δF)", bg=UI['sidebar'], fg=UI['accent']).pack(anchor='w', padx=20)
        self.slider_df = tk.Scale(self.sidebar, from_=0.01, to=0.50, resolution=0.01, orient='horizontal',
                                  bg=UI['sidebar'], fg='white', highlightthickness=0, command=lambda x: self._simuler())
        self.slider_df.set(0.10)
        self.slider_df.pack(fill='x', padx=20, pady=10)

        self.check_vars = {}
        for k in CATS_MAP.keys():
            v = tk.BooleanVar(value=True)
            self.check_vars[k] = v
            tk.Checkbutton(self.sidebar, text=k, variable=v, bg=UI['sidebar'], fg='white', selectcolor=UI['sidebar'], command=self._simuler).pack(anchor='w', padx=30)

        tk.Button(self.sidebar, text="💾 Exporter Graphes (PNG)", command=self._save_pop_plots, bg=UI['accent'], fg='white', pady=10).pack(side='bottom', fill='x', padx=20, pady=20)

        # Tabs
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # TAB 1: VISUALISATION
        self.tab_vis = tk.Frame(self.tabs, bg='white')
        self.tabs.add(self.tab_vis, text=" 📈 Évolutions des populations ")
        
        self.fig_vis = Figure(figsize=(10, 8), dpi=100)
        self.canvas_vis = FigureCanvasTkAgg(self.fig_vis, master=self.tab_vis)
        self.canvas_vis.get_tk_widget().pack(fill='both', expand=True)

        # TAB 2: ANALYSE & ECARTS
        self.tab_ana = tk.Frame(self.tabs, bg='white')
        self.tabs.add(self.tab_ana, text=" 📑 Analyse détaillée ")
        self._build_analysis_ui()

    def _build_analysis_ui(self):
        f_audit = tk.LabelFrame(self.tab_ana, text=" Audit ponctuel par année ", bg='white')
        f_audit.pack(fill='x', padx=15, pady=5)
        
        tk.Label(f_audit, text="Année :", bg='white').pack(side='left', padx=5, pady=5)
        self.an_audit = tk.Spinbox(f_audit, from_=2000, to=2024, width=8)
        self.an_audit.pack(side='left', padx=5)
        tk.Button(f_audit, text="Comparer", command=self._update_audit_table, bg=UI['sidebar'], fg='white').pack(side='left', padx=10)
        tk.Button(f_audit, text="📥 Excel Audit", command=self._export_audit_excel, bg='#0F172A', fg='white').pack(side='left', padx=5)

        self.tree_audit = ttk.Treeview(f_audit, columns=("cat", "est", "reel", "ecart"), show='headings', height=6)
        for c, t in zip(("cat", "est", "reel", "ecart"), ("Catégorie", "Estimé (M)", "Réel (M)", "Écart Relatif (%)")):
            self.tree_audit.heading(c, text=t); self.tree_audit.column(c, anchor="center")
        self.tree_audit.pack(fill='x', padx=10, pady=5)

        self.f_temp = tk.LabelFrame(self.tab_ana, text=" Analyse temporelle des écarts ", bg='white')
        self.f_temp.pack(fill='both', expand=True, padx=15, pady=5)

        ctrl = tk.Frame(self.f_temp, bg='white')
        ctrl.pack(fill='x', padx=10, pady=5)
        self.cat_select = ttk.Combobox(ctrl, values=list(CATS_MAP.keys()), state="readonly", width=22)
        self.cat_select.current(0); self.cat_select.pack(side='left', padx=5)
        
        self.an_deb = tk.Entry(ctrl, width=5); self.an_deb.insert(0, "2000"); self.an_deb.pack(side='left')
        tk.Label(ctrl, text="-", bg='white').pack(side='left')
        self.an_fin = tk.Entry(ctrl, width=5); self.an_fin.insert(0, "2024"); self.an_fin.pack(side='left')
        
        tk.Button(ctrl, text="🔍 Actualiser", command=self._update_error_plot, bg=UI['sidebar'], fg='white').pack(side='left', padx=5)
        
        self.show_table = tk.BooleanVar(value=False)
        self.btn_toggle = tk.Button(ctrl, text="📋 Voir Tableau", command=self._toggle_table, bg=UI['button_alt'], fg='white')
        self.btn_toggle.pack(side='left', padx=5)

        tk.Button(ctrl, text="💾 Exporter PNG", command=self._save_error_plot, bg='#475569', fg='white').pack(side='right', padx=2)
        tk.Button(ctrl, text="📥 Exporter Excel", command=self._export_temp_excel, bg='#0F172A', fg='white').pack(side='right', padx=2)

        self.table_container = tk.Frame(self.f_temp, bg='white')
        self.tree_temp = ttk.Treeview(self.table_container, columns=("an", "vest", "vreel", "err"), show='headings', height=5)
        self.tree_temp.heading("an", text="Année"); self.tree_temp.heading("vest", text="Estimé (M)"); 
        self.tree_temp.heading("vreel", text="Réel (M)"); self.tree_temp.heading("err", text="Écart %")
        for col in ("an", "vest", "vreel", "err"): self.tree_temp.column(col, width=95, anchor="center")
        self.tree_temp.pack(side='left', fill='y', padx=(10,0))
        
        self.fig_err = Figure(figsize=(6, 3), dpi=95)
        self.canvas_err = FigureCanvasTkAgg(self.fig_err, master=self.f_temp)
        self.canvas_err.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=5)

    def _toggle_table(self):
        if self.show_table.get():
            self.table_container.pack_forget()
            self.btn_toggle.config(text="📋 Voir Tableau")
            self.show_table.set(False)
        else:
            self.table_container.pack(side='left', fill='y', before=self.canvas_err.get_tk_widget())
            self.btn_toggle.config(text="❌ Masquer Tableau")
            self.show_table.set(True)

    def _simuler(self):
        if self.df_reel is None: return
        p = PARAMS_DEF.copy(); p['delta_F'] = self.slider_df.get()
        r0 = self.df_reel[self.df_reel['Année'] == 2000].iloc[0]
        Y0 = np.array([r0['M'], r0['F'], r0['FP'], r0['JM'], r0['JF']])
        t, y = resoudre_rk4(Y0, p)
        self.res = {'t': t + 2000, 'y': y, 'total': y.sum(axis=1)}
        self._update_vis_plots()
        self._update_audit_table()
        self._update_error_plot()

    def _update_vis_plots(self):
        self.fig_vis.clear()
        # Titre incluant le paramètre
        self.fig_vis.suptitle(f"SIMULATION DE L'ÉVOLUTION DU CHEPTEL OVIN (δF = {self.slider_df.get():.2f})", 
                             fontsize=13, fontweight='bold', color=UI['sidebar'])
        
        # Ajout de la légende DANS la figure pour l'export PNG
        self.fig_vis.text(0.5, 0.92, "LÉGENDE : ── Ligne verte = Estimations | ●● Points gris = Données réelles", 
                          ha='center', fontsize=10, style='italic', color='#475569')

        selected = [lbl for lbl, v in self.check_vars.items() if v.get()]
        if not selected: self.canvas_vis.draw(); return
        
        cols = 2 if len(selected) <= 4 else 3
        rows = int(np.ceil(len(selected) / cols))
        
        for i, lbl in enumerate(selected):
            ax = self.fig_vis.add_subplot(rows, cols, i+1)
            key = CATS_MAP[lbl]
            y_sim = self.res['total'] if key == 'Total' else self.res['y'][:, ['M','F','FP','JM','JF'].index(key)]
            col_r = 'Effectif' if key == 'Total' else key
            
            y_ann = y_sim[::100][:len(self.df_reel)]
            v_r = self.df_reel[col_r].values[:len(y_ann)]
            err_m = np.mean(np.abs(y_ann - v_r) / (v_r + 1)) * 100

            ax.plot(self.res['t'], y_sim/1e6, color=UI['accent'], lw=1.8)
            ax.scatter(self.df_reel['Année'], self.df_reel[col_r]/1e6, color=UI['real'], s=12, alpha=0.5)
            ax.set_title(f"{lbl}\nÉcart relatif moyen : {err_m:.2f}%", fontsize=9, fontweight='bold')
            ax.grid(True, alpha=0.1)
        
        self.fig_vis.tight_layout(rect=[0, 0, 1, 0.90]) # Ajustement pour laisser place au titre/légende
        self.canvas_vis.draw()

    def _update_audit_table(self):
        try: an = int(self.an_audit.get())
        except: return
        for i in self.tree_audit.get_children(): self.tree_audit.delete(i)
        row_r = self.df_reel[self.df_reel['Année'] == an]
        if row_r.empty: return
        idx_s = np.argmin(np.abs(self.res['t'] - an))
        for lbl, key in CATS_MAP.items():
            v_r = row_r.iloc[0]['Effectif' if key == 'Total' else key]
            v_s = self.res['total'][idx_s] if key == 'Total' else self.res['y'][idx_s, ['M','F','FP','JM','JF'].index(key)]
            ecart = ((v_s - v_r) / (v_r + 1)) * 100
            self.tree_audit.insert("", "end", values=(lbl, f"{v_s/1e6:.3f}", f"{v_r/1e6:.3f}", f"{ecart:+.2f} %"))

    def _update_error_plot(self):
        try: deb, fin = int(self.an_deb.get()), int(self.an_fin.get())
        except: return
        cat_lbl = self.cat_select.get(); key = CATS_MAP[cat_lbl]
        col_r = 'Effectif' if key == 'Total' else key
        df_f = self.df_reel[(self.df_reel['Année'] >= deb) & (self.df_reel['Année'] <= fin)]
        
        for i in self.tree_temp.get_children(): self.tree_temp.delete(i)
        errs = []
        for _, row in df_f.iterrows():
            idx = np.argmin(np.abs(self.res['t'] - row['Année']))
            v_s = self.res['total'][idx] if key == 'Total' else self.res['y'][idx, ['M','F','FP','JM','JF'].index(key)]
            vr = row[col_r]
            e = ((v_s - vr) / (vr + 1)) * 100
            errs.append(e)
            self.tree_temp.insert("", "end", values=(int(row['Année']), f"{v_s/1e6:.3f}", f"{vr/1e6:.3f}", f"{e:+.2f}%"))

        self.fig_err.clear()
        ax = self.fig_err.add_subplot(111)
        ax.axhline(0, color='black', lw=0.8, ls='--')
        ax.plot(df_f['Année'], errs, marker='o', color=UI['danger'], lw=1.5, markersize=4)
        ax.set_title(f"Profil des écarts relatifs : {cat_lbl}", fontsize=10)
        ax.set_ylabel("Écart relatif (%)")
        ax.grid(True, alpha=0.2); self.fig_err.tight_layout(); self.canvas_err.draw()

    def _save_pop_plots(self):
        df_val = self.slider_df.get()
        p = filedialog.asksaveasfilename(defaultextension=".png", 
                                         initialfile=f"Evolution_Population_Ovine_deltaF_{df_val:.2f}.png")
        if p: self.fig_vis.savefig(p, dpi=300); messagebox.showinfo("Succès", "Graphique sauvegardé avec légende.")

    def _save_error_plot(self):
        cat = self.cat_select.get().replace(" ", "_")
        p = filedialog.asksaveasfilename(defaultextension=".png", 
                                         initialfile=f"Ecarts_Temporels_{cat}.png")
        if p: self.fig_err.savefig(p, dpi=300); messagebox.showinfo("Succès", "Profil d'erreur sauvegardé.")

    def _export_audit_excel(self):
        an = self.an_audit.get()
        p = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"Audit_Ovin_{an}.xlsx")
        if p:
            data = [self.tree_audit.item(i)['values'] for i in self.tree_audit.get_children()]
            df = pd.DataFrame(data, columns=["Catégorie", "Estimé (M)", "Réel (M)", "Écart Relatif (%)"])
            df.to_excel(p, index=False)
            messagebox.showinfo("Export", f"Audit de l'année {an} exporté.")

    def _export_temp_excel(self):
        cat = self.cat_select.get().replace(" ", "_")
        p = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"Evolution_Ecarts_{cat}.xlsx")
        if p:
            data = [self.tree_temp.item(i)['values'] for i in self.tree_temp.get_children()]
            df = pd.DataFrame(data, columns=["Année", "Estimé (M)", "Réel (M)", "Écart %"])
            df.to_excel(p, index=False)
            messagebox.showinfo("Export", f"Série temporelle pour {cat} exportée.")

if __name__ == "__main__":
    app = SimulateurOvinV9(); app.mainloop()