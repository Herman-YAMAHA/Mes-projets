# Etape 1 : Configuration du projet

from pathlib import Path


chemin_code = Path("C:/Users/DELL/Desktop/ENSAE/ISEP3/Semestre 1/Calcul scientifique/Projet de CS/Projet_CS_Ovins_Groupe_5/script")


chemin_projet = chemin_code.parent

# Définition dynamique des sous-dossiers
chemin_data    = chemin_projet / 'data'
chemin_outputs = chemin_projet / 'outputs'

print("Code   :", chemin_code)
print("Projet :", chemin_projet)


# Création des dossiers s'ils n'existent pas
for dossier in [chemin_data, chemin_code, chemin_outputs]:
    dossier.mkdir(parents=True, exist_ok=True)

# Vérification
print(f"Racine du projet  : {chemin_projet}")
print(f"Dossier data      : {chemin_data}")
print(f"Dossier code      : {chemin_code}")
print(f"Dossier outputs   : {chemin_outputs}")


# Etape 2 : Chargement de la base

import pandas as pd

# Chargement dynamique de la base
chemin_base = chemin_data / 'base_ovins_complete.xlsx'
df = pd.read_excel(chemin_base)

print(f"Base chargée depuis : {chemin_base}")
print(f"Dimensions : {df.shape[0]} lignes x {df.shape[1]} colonnes")
print(f"\nVariables disponibles :\n{list(df.columns)}")


# Etape 3 : Définition des libellés

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
    'TN'         : 'Total des naissances',
    'Année'      : 'Année',
    'Objet'      : 'Le groupe d\'animal',
    'Pays'       : 'Le pays'
}

# Stockage des libellés dans les attributs du DataFrame
df.attrs['labels'] = labels

# Affichage
print("Libellés définis avec succès :\n")
for var, label in labels.items():
    print(f"  {var:<15} → {label}")
    
    

# Etape 4 : Sauvegarde de la base nettoyée

# Chemin dynamique de sauvegarde
output_path = chemin_data / 'base_ovins_nettoyee.xlsx'

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:

    # Onglet données
    df.to_excel(writer, sheet_name='Données', index=False)

    # Onglet métadonnées
    df_labels = pd.DataFrame(
        list(labels.items()),
        columns=['Variable', 'Libellé']
    )
    df_labels.to_excel(writer, sheet_name='Métadonnées', index=False)

print(f"Base sauvegardée dans : {output_path}")