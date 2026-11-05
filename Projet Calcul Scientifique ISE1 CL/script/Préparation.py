import os
import pandas as pd
from pathlib import Path

# ============================================================
# ÉTAPE 1 : CONFIGURATION AUTOMATIQUE
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
# ÉTAPE 2 : CHARGEMENT DE LA BASE
# ============================================================
chemin_base = chemin_data / 'base_ovins_complete.xlsx'

if not chemin_base.exists():
    raise FileNotFoundError(f"❌ Le fichier {chemin_base.name} est absent du dossier data.")

df = pd.read_excel(chemin_base)

print(f"\n Base chargée : {df.shape[0]} lignes x {df.shape[1]} colonnes")

# ============================================================
# ÉTAPE 3 : DÉFINITION DES LIBELLÉS
# ============================================================
labels = {
    'taux_mat_m' : 'Taux de maturation des jeunes mâles',
    'mort_m'     : 'Taux de mortalité naturel des mâles matures',
    'prelev_m'   : 'Taux de prélèvement social des mâles',
    'taux_mat_f' : 'Taux de maturation des jeunes femelles',
    'const_app'  : 'Constante d\'appariement',
    'mort_f'     : 'Taux de mortalité naturelle des femelles matures',
    'abat_m'     : 'Taux d\'abattage des mâles',
    'abat_f'     : 'Taux d\'abattage des femelles',
    'mise_bas'   : 'Taux de mise bas',
    'mort_fg'    : 'Taux de mortalité naturelle des femelles gestantes',
    'nais_m'     : 'Taux de naissance des mâles',
    'mort_jm'    : 'Taux de mortalité naturelle des jeunes mâles',
    'nais_f'     : 'Taux de naissance des femelles',
    'mort_jf'    : 'Taux de mortalité naturelle des jeunes femelles',
    'taf'        : 'Taux d\'appariement fertile',
    'JM'         : 'Jeunes mâles',
    'JF'         : 'Jeunes femelles',
    'M'          : 'Mâles matures',
    'F'          : 'Femelles matures non gestantes',
    'FP'         : 'Femelles matures gestantes',
    'TA'         : 'Têtes abattues',
    'Effectif'   : 'Effectif total',
    'Année'      : 'Année',
    'Objet'      : 'Le groupe d\'animal',
    'Pays'       : 'Le pays'
}

# Stockage dans les métadonnées du DataFrame
df.attrs['labels'] = labels

print("\n Métadonnées enregistrées avec succès.")

# ============================================================
# ÉTAPE 4 : SAUVEGARDE DE LA BASE NETTOYÉE
# ============================================================
output_path = chemin_data / 'base_ovins_nettoyee.xlsx'

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    # Onglet des données brutes
    df.to_excel(writer, sheet_name='Données', index=False)

    # Onglet des métadonnées pour la compréhension des variables
    df_labels = pd.DataFrame(list(labels.items()), columns=['Variable', 'Libellé'])
    df_labels.to_excel(writer, sheet_name='Métadonnées', index=False)

print(f"\n Sauvegarde terminée : {output_path}")