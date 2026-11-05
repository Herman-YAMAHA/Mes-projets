import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from pathlib import Path
import os

# ============================================================
# 0. CONFIGURATION DES CHEMINS
# ============================================================
NOM_PROJET = "Projet_CS_Ovins_Groupe_5"

def localiser_projet():
    # Test 1 : Est-on déjà dans le dossier ou un sous-dossier ?
    chemin_actuel = Path.cwd()
    for parent in [chemin_actuel] + list(chemin_actuel.parents):
        if parent.name == NOM_PROJET:
            return parent

    # Test 2 : Scan du Bureau et des Documents (pour les collègues)
    search_paths = [Path.home() / "Desktop", Path.home() / "Documents"]
    for p in search_paths:
        found = list(p.glob(f"**/{NOM_PROJET}"))
        if found:
            return found[0]
    return None

racine_detectee = localiser_projet()

if not racine_detectee:
    raise FileNotFoundError(f"❌ Impossible de localiser le dossier '{NOM_PROJET}'. "
                            "Veuillez le placer sur votre Bureau ou dans vos Documents.")

# On force Spyder à se placer à la racine du projet
os.chdir(racine_detectee)

# Définition dynamique des chemins
chemin_projet  = racine_detectee
chemin_data    = chemin_projet / 'data'
chemin_code    = chemin_projet / 'script'
chemin_outputs = chemin_projet / 'outputs'

# Création des dossiers manquants
for dossier in [chemin_data, chemin_outputs]:
    dossier.mkdir(parents=True, exist_ok=True)

print(f"Configuration réussie !")
print(f" Racine : {chemin_projet}")

# ============================================================
# 1. CHARGEMENT DES DONNEES
# ============================================================
chemin_base = chemin_data / 'base_ovins_nettoyee.xlsx'

if not chemin_base.exists():
    raise FileNotFoundError(f"❌ Le fichier {chemin_base.name} est introuvable.")

df = pd.read_excel(chemin_base)

# ============================================================
# 2. PARAMETRES DU MODELE
# ============================================================
params = {
    'gm'      : 0.25,   # Taux de maturation des jeunes males
    'gf'      : 0.90,   # Taux de maturation des jeunes femelles
    'mu_M'    : 0.21,   # Mortalite naturelle des males matures
    'tau_M'   : 0.01,   # Prelevement social des males
    'tau_F'   : 0.001,  # Prelevement social des femelles
    'mu_F'    : 0.11,   # Mortalite naturelle des femelles matures
    'delta_M' : 0.20,   # Taux d'abattage des males
    'delta_F' : 0.10,   # Taux d'abattage des femelles
    'd'       : 1.15,   # Taux de mise bas
    'mu_Fp'   : 0.15,   # Mortalite naturelle des femelles gestantes
    'lambda_m': 0.432,  # Taux de naissance des males
    'lambda_f': 0.598,  # Taux de naissance des femelles
    'mu_m'    : 0.171,  # Mortalite naturelle des jeunes males
    'mu_f'    : 0.134,  # Mortalite naturelle des jeunes femelles
    'k'       : 60000,  # Constante d'appariement
}

# ============================================================
# 3. FONCTIONS DU SYSTEME DYNAMIQUE
# ============================================================
def appariement(M, F, k):
    return F * M / (M + k) if (M + k) != 0 else 0

def systeme(t, Y, p):
    M, F, Fp, JM, JF = Y
    f = appariement(M, F, p['k'])

    dM  = p['gm'] * JM - (p['mu_M'] + p['tau_M'] + p['delta_M']) * M
    dF  = p['gf'] * JF - f - (p['mu_F'] + p['tau_F'] + p['delta_F']) * F + p['d'] * Fp
    dFp = f - (p['d'] + p['mu_Fp']) * Fp
    dJM = p['lambda_m'] * Fp - (p['gm'] + p['mu_m']) * JM
    dJF = p['lambda_f'] * Fp - (p['gf'] + p['mu_f']) * JF

    return np.array([dM, dF, dFp, dJM, dJF])

def runge_kutta_4(f, t0, tf, Y0, h, p):
    t_vals, Y_vals = [t0], [Y0.copy()]
    t, Y = t0, Y0.copy()
    while t < tf:
        k1 = f(t, Y, p)
        k2 = f(t + h/2, Y + h/2*k1, p)
        k3 = f(t + h/2, Y + h/2*k2, p)
        k4 = f(t + h, Y + h*k3, p)
        Y += (h/6) * (k1 + 2*k2 + 2*k3 + k4)
        t += h
        t_vals.append(t)
        Y_vals.append(Y.copy())
    return np.array(t_vals), np.array(Y_vals)

# ============================================================
# 4. RESOLUTION NUMERIQUE
# ============================================================
Y0 = df.loc[df['Année'] == 2000, ['M', 'F', 'FP', 'JM', 'JF']].values[0].astype(float)
t_sol, Y_sol = runge_kutta_4(systeme, 0, 24, Y0, 0.01, params)

annees_sol = t_sol + 2000
N_sol = Y_sol.sum(axis=1)

# Calcul des ecarts
pas = int(100) # Correspond a h=0.01 pour echantillonnage annuel
Y_annuel = Y_sol[::pas][:len(df)]
ecarts = {var: np.abs((Y_annuel[:, i] - df[var].values) / (df[var].values + 1)).mean() * 100 
          for i, var in enumerate(['M', 'F', 'FP', 'JM', 'JF'])}

# ============================================================
# 5. GRAPHIQUE C-a : MODELE VS REEL
# ============================================================
plt.rcParams.update({
    'figure.dpi': 150, 
    'font.family': 'DejaVu Sans', 
    'axes.spines.top': False, 
    'axes.spines.right': False
})

fig, axes = plt.subplots(2, 3, figsize=(15, 9))
axes = axes.flatten()

labels_plots = [
    ('M', 'Males matures', 'steelblue'), 
    ('F', 'Femelles non gestantes', 'darkorange'),
    ('FP', 'Femelles gestantes', 'green'), 
    ('JM', 'Jeunes males', 'red'),
    ('JF', 'Jeunes femelles', 'purple')
]

for i, (var, titre, couleur) in enumerate(labels_plots):
    ax = axes[i]
    ax.plot(annees_sol, Y_sol[:, i] / 1e6, color=couleur, linewidth=2, label='Modele RK4')
    ax.scatter(df['Année'], df[var] / 1e6, color='black', s=20, zorder=5, label='Reel')
    
    ax.set_title(titre)
    # Axe X : Pas de 4 ans, valeurs entieres
    ax.set_xticks(np.arange(2000, 2025, 4))
    ax.set_xlabel("Annee")
    ax.set_ylabel("Millions de tetes")
    ax.legend(fontsize=8)
    ax.grid(axis='y', alpha=0.3)

# Panneau total (Effectif total)
ax_tot = axes[5]
ax_tot.plot(annees_sol, N_sol / 1e6, color='navy', linewidth=2, label='Modele RK4')
ax_tot.scatter(df['Année'], df['Effectif'] / 1e6, color='black', s=20, zorder=5, label='Reel')
ax_tot.set_title("Effectif total")
ax_tot.set_xticks(np.arange(2000, 2025, 4))
ax_tot.set_xlabel("Annee")
ax_tot.set_ylabel("Millions de tetes")
ax_tot.legend(fontsize=8)
ax_tot.grid(axis='y', alpha=0.3)

plt.suptitle("Validation du modèle RK4 (2000-2024)", fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(chemin_outputs / 'graphique_Ca_modele_vs_reel.png', bbox_inches='tight')
plt.show()

# ============================================================
# 6. GRAPHIQUE C-b : VARIATION ABATTAGE FEMELLES
# ============================================================
taux_tests = [0.05, 0.10, 0.20, 0.30, 0.50]
plt.figure(figsize=(10, 6))

# Simulation et tracé pour chaque taux
for delta_F in taux_tests:
    p_v = params.copy()
    p_v['delta_F'] = delta_F
    # Simulation sur 20 ans (jusqu'a 2020)
    t_v, Y_v = runge_kutta_4(systeme, 0, 20, Y0, 0.01, p_v)
    plt.plot(t_v + 2000, Y_v.sum(axis=1) / 1e6, label=f'delta_F = {delta_F:.2f}', linewidth=1.8)

# Ajout de la courbe des données réelles pour comparaison (jusqu'en 2020)
df_filtre = df[df['Année'] <= 2020]
plt.scatter(df_filtre['Année'], df_filtre['Effectif'] / 1e6, 
            color='black', s=30, zorder=10, label='Donnees reelles')

plt.title("Impact du taux d'abattage des femelles sur l'effectif total (2000-2020)", fontweight='bold')
plt.xlabel("Annee")
plt.ylabel("Effectif (millions de tetes)")

# Axe X : Pas de 2 ans, valeurs entieres
plt.xticks(np.arange(2000, 2021, 2))

plt.legend(title="Scenarios", fontsize=9)
plt.grid(axis='y', alpha=0.3)
plt.gca().spines['top'].set_visible(False)
plt.gca().spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(chemin_outputs / 'graphique_Cb_variation_abattage.png', bbox_inches='tight')
plt.show()

print(f"Graphiques sauvegardés dans : {chemin_outputs}")