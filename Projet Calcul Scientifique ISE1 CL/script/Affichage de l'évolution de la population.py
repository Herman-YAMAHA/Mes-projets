import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

# ============================================================
# ETAPE 1 : CONFIGURATION DES CHEMINS 
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
# 2. CHARGEMENT DE LA BASE NETTOYEE
# ============================================================
chemin_base = chemin_data / 'base_ovins_nettoyee.xlsx'

if not chemin_base.exists():
    raise FileNotFoundError(f"❌ Le fichier {chemin_base.name} est absent. Verifiez l'etape precedente.")

df = pd.read_excel(chemin_base)
annees = df['Année']

# ============================================================
# 3. PARAMETRES GRAPHIQUES GLOBAUX
# ============================================================
plt.rcParams.update({
    'font.family'       : 'DejaVu Sans',
    'font.size'         : 11,
    'axes.titlesize'    : 13,
    'axes.titleweight'  : 'bold',
    'axes.labelsize'    : 11,
    'axes.spines.top'   : False,
    'axes.spines.right' : False,
    'legend.fontsize'   : 10,
    'figure.dpi'        : 150
})

# ============================================================
# GRAPHIQUE 1 : Evolution de l'effectif total
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(annees, df['Effectif'] / 1e6,
        color='steelblue', linewidth=2.2, marker='o', markersize=4)
ax.fill_between(annees, df['Effectif'] / 1e6, alpha=0.08, color='steelblue')

ax.set_title("Evolution de l'effectif total du cheptel ovin au Sénégal (2000–2024)")
ax.set_xlabel("Annee")
ax.set_ylabel("Effectif (en millions de tetes)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f} M'))
ax.set_xticks(annees[::2])
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig(chemin_outputs / 'graphique1_effectif_total.png', bbox_inches='tight')
plt.show()

# ============================================================
# GRAPHIQUE 2 : Evolution par classe d'âge (Jeunes vs Adultes)
# ============================================================
df['Jeunes']  = df['JM'] + df['JF']
df['Adultes'] = df['M']  + df['F'] + df['FP']

fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(annees, df['Jeunes']  / 1e6, color='darkorange',
        linewidth=2.2, marker='o', markersize=4, label='Jeunes (≤ 1 an)')
ax.plot(annees, df['Adultes'] / 1e6, color='steelblue',
        linewidth=2.2, marker='s', markersize=4, label='Adultes (> 1 an)')

ax.set_title("Evolution du cheptel ovin par classe d'âge au Sénégal (2000–2024)")
ax.set_xlabel("Annee")
ax.set_ylabel("Effectif (en millions de tetes)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f} M'))
ax.set_xticks(annees[::2])
ax.tick_params(axis='x', rotation=45)
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig(chemin_outputs / 'graphique2_classes_age.png', bbox_inches='tight')
plt.show()

# ============================================================
# GRAPHIQUE 3 : Evolution des 5 compartiments
# ============================================================
compartiments = {
    'M'  : ('Males matures',                'steelblue'),
    'F'  : ('Femelles matures non gestantes','darkorange'),
    'FP' : ('Femelles gestantes',            'green'),
    'JM' : ('Jeunes males',                 'red'),
    'JF' : ('Jeunes femelles',              'purple'),
}

fig, ax = plt.subplots(figsize=(11, 6))

for var, (label, couleur) in compartiments.items():
    ax.plot(annees, df[var] / 1e6,
            label=label, color=couleur, linewidth=2, marker='o', markersize=3)

ax.set_title("Evolution des 5 compartiments du cheptel ovin au Sénégal (2000–2024)")
ax.set_xlabel("Annee")
ax.set_ylabel("Effectif (en millions de tetes)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.2f} M'))
ax.set_xticks(annees[::2])
ax.tick_params(axis='x', rotation=45)
ax.legend(loc='upper left')
ax.grid(axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig(chemin_outputs / 'graphique3_compartiments.png', bbox_inches='tight')
plt.show()


# ============================================================
# GRAPHIQUE 4 : Evolution des abattages
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))

# On ne garde que la serie des abattages (TA)
ax.plot(annees, df['TA'] / 1e6, color='crimson',
        linewidth=2.2, marker='s', markersize=4, label='Total abattages')

# Remplissage leger sous la courbe pour ameliorer le rendu visuel
ax.fill_between(annees, df['TA'] / 1e6, alpha=0.08, color='crimson')

ax.set_title("Evolution des abattages de moutons au Sénégal (2000–2024)")
ax.set_xlabel("Annee")
ax.set_ylabel("Effectif (en millions de tetes)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f} M'))
ax.set_xticks(annees[::2])
ax.tick_params(axis='x', rotation=45)
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig(chemin_outputs / 'graphique4_abattages.png', bbox_inches='tight')
plt.show()