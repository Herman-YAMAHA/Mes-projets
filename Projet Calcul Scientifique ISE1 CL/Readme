# Dynamique du cheptel ovin au Sénégal : modélisation par EDO et résolution Runge-Kutta d'ordre 4

**Calibrage d'un modèle à cinq compartiments sur les données FAOSTAT (2000–2024) et analyse de l'impact du taux d'abattage des femelles**

Projet de Calcul Scientifique — ISE1, ENSAE Pierre Ndiaye (Dakar) — Année académique 2025–2026

| | |
|---|---|
| **Groupe** | Groupe 5 |
| **Auteurs** | Cheikh THIOUB (ISE1 – Cycle Long) · Herman Parfait NGAKE YAMAHA (ISE1 – Cycle Long) · Cheikh Mouhamadou Moustapha NDIAYE (ISE1 – Cycle Long) · Lancine KEITA (ISE1 – Mathématiques) |
| **Encadrement** | M. Omar DIOP, enseignant-chercheur en mathématiques |
| **Langage** | Python (pandas, NumPy, Matplotlib, Tkinter) |
| **Données** | FAOSTAT (cheptel ovin du Sénégal, 2000–2024) et littérature zootechnique |
| **Langue du rapport** | Français |

---

## Table des matières

1. [Contexte et objectif](#1-contexte-et-objectif)
2. [Contenu du dépôt](#2-contenu-du-dépôt)
3. [Le modèle](#3-le-modèle)
4. [Paramètres](#4-paramètres)
5. [Principaux résultats](#5-principaux-résultats)
6. [Prérequis et exécution](#6-prérequis-et-exécution)
7. [Simulateur interactif](#7-simulateur-interactif)
8. [Sorties produites](#8-sorties-produites)
9. [Limites et points d'attention](#9-limites-et-points-dattention)
10. [Sources](#10-sources)
11. [Citation](#11-citation)

---

## 1. Contexte et objectif

L'élevage ovin est une activité agropastorale majeure au Sénégal : selon le RNA (ANSD, 2018-2019), près de 32 % des ménages ruraux le pratiquent, et le cheptel est passé d'environ 4,5 millions de têtes en 2000 à environ 8,7 millions en 2024 (FAOSTAT). La demande exceptionnelle liée à la Tabaski, la mortalité juvénile, la variabilité climatique et l'abattage de femelles reproductrices font peser des tensions structurelles sur la durabilité des troupeaux.

Le projet poursuit un double objectif :

1. **Calibrer** un système de cinq équations différentielles ordinaires (EDO) sur les données réelles 2000–2024.
2. **Résoudre** ce système par la méthode de **Runge-Kutta d'ordre 4 (RK4)** et analyser l'effet de la variation du **taux d'abattage des femelles (δF)** sur la viabilité à long terme du cheptel.

## 2. Contenu du dépôt

```
Projet_CS_Ovins_Groupe_5/
├── Rapport.pdf                                          # Rapport (11 pages)
├── README.md
├── data/
│   ├── base_ovins_complete.xlsx                         # Base brute (25 lignes × 25 variables, 2000–2024)
│   ├── base_ovins_nettoyee.xlsx                         # Base libellée (onglets « Données » et « Métadonnées »)
│   └── Parametre_repartition de la population en catégorie.xlsx   # Proportions initiales par compartiment et sources
├── script/
│   ├── Préparation.py                                   # Localisation du projet, libellés, base nettoyée
│   ├── Affichage de l'évolution de la population.py     # Graphiques descriptifs (graphiques 1 à 4)
│   ├── Resolution par la méthode Runge-Kutta d'ordre 4.py  # Modèle, RK4, validation, scénarios δF
│   ├── API.py                                           # Simulateur interactif (Tkinter)
│   ├── script.py                                        # Version initiale de la préparation (chemin local figé)
│   └── notebook.ipynb                                   # Notebook (configuration des chemins uniquement)
└── outputs/                                             # Graphiques PNG
```

La base contient, par année : l'effectif total, les têtes abattues (`TA`), les cinq compartiments (`JM`, `JF`, `M`, `F`, `FP`) et les taux biologiques associés.

## 3. Le modèle

### 3.1 Compartiments

| Symbole | Compartiment |
|---|---|
| `M` | Mâles matures (> 1 an) |
| `F` | Femelles matures non gestantes |
| `Fp` | Femelles gestantes |
| `JM` | Jeunes mâles (0–1 an) |
| `JF` | Jeunes femelles (0–1 an) |

La population est répartie en deux classes d'âge : **jeunes** (≤ 1 an) et **adultes** (> 1 an), seuil cohérent avec une maturité sexuelle à 8–12 mois chez les races locales (Peul-Peul, Touabire).

### 3.2 Système d'EDO

Tel qu'implémenté dans `Resolution par la méthode Runge-Kutta d'ordre 4.py` :

```
f(M, F)  = F · M / (M + k)                                  # fonction d'appariement

dM/dt   = g_m · JM − (μ_M + τ_M + δ_M) · M
dF/dt   = g_f · JF − f(M, F) − (μ_F + τ_F + δ_F) · F + d · Fp
dFp/dt  = f(M, F) − (d + μ_Fp) · Fp
dJM/dt  = λ_m · Fp − (g_m + μ_m) · JM
dJF/dt  = λ_f · Fp − (g_f + μ_f) · JF
```

Les naissances proviennent exclusivement des femelles gestantes (`Fp`), ce qui explique la forte sensibilité du système au taux d'abattage des femelles.

### 3.3 Résolution numérique

- Méthode : **Runge-Kutta d'ordre 4** (erreur locale en O(h⁵), globale en O(h⁴)).
- Pas de temps : **h = 0,01 an** (100 sous-intervalles par an).
- Horizon : 24 ans (2000–2024) pour la validation, 20 ans (2000–2020) pour les scénarios d'abattage.
- Condition initiale : valeurs observées en 2000 pour les cinq compartiments.

### 3.4 Mesure d'adéquation

Écart relatif moyen par compartiment *c* sur *T* = 25 années :

```
ε_c = (1/T) · Σ_t | Y_c^modèle(t) − Y_c^réel(t) | / Y_c^réel(t) × 100
```

## 4. Paramètres

Quatorze paramètres biologiques et la constante d'appariement *k* sont utilisés. Ils sont classés selon la fiabilité de leur source.

| Paramètre | Description | Valeur | Statut |
|---|---|---|---|
| `d` | Taux de mise bas | 1,15 | Sourcé (Clément et al., 1997) |
| `λ_m` | Taux de naissance des mâles | 0,432 | Calculé (FAOSTAT) |
| `λ_f` | Taux de naissance des femelles | 0,598 | Calculé (FAOSTAT) |
| `μ_m` | Mortalité naturelle des jeunes mâles | 0,171 | Sourcé (Akpo et al.) |
| `μ_f` | Mortalité naturelle des jeunes femelles | 0,134 | Sourcé (Akpo et al.) |
| `g_m` | Maturation des jeunes mâles | 0,25 | Proxy |
| `g_f` | Maturation des jeunes femelles | 0,90 | Proxy |
| `μ_M` | Mortalité naturelle des mâles matures | 0,21 | Proxy |
| `μ_F` | Mortalité naturelle des femelles matures | 0,11 | Proxy |
| `μ_Fp` | Mortalité des femelles gestantes | 0,15 | Proxy |
| `τ_M` | Prélèvement social des mâles | 0,01 | Arbitraire |
| `τ_F` | Prélèvement social des femelles | 0,001 | Arbitraire |
| `δ_M` | Taux d'abattage des mâles | 0,20 | Arbitraire (cohérent avec MEPA, 2022) |
| `δ_F` | Taux d'abattage des femelles | 0,10 | Arbitraire (cohérent avec MEPA, 2022) |
| `k` | Constante d'appariement | 60 000 | Arbitraire |

**Répartition initiale de la population (2000)**, d'après Buldgen, Dieng et al. (FAO/INDR Thiès) et Hamadou et al. (2021) :

| JM | JF | M | F | Fp |
|---|---|---|---|---|
| 21,98 % | 30,13 % | 2,96 % | 27,41 % | 17,52 % |

Les paramètres « proxy » et « arbitraire » constituent une limite méthodologique explicite du modèle (voir [section 9](#9-limites-et-points-dattention)).

## 5. Principaux résultats

> Les chiffres ci-dessous sont ceux du rapport (`Rapport.pdf`).

### 5.1 Qualité d'ajustement du modèle (2000–2024)

| Compartiment | Écart relatif moyen |
|---|---|
| Effectif total | 5,1 % |
| JM (jeunes mâles) | 4,3 % |
| F (femelles non gestantes) | 20,2 % |
| Fp (femelles gestantes) | 28,9 % |
| JF (jeunes femelles) | 53,9 % |
| M (mâles matures) | 282,0 % |

- Le modèle reproduit **bien la tendance globale** du cheptel (effectif total) : il le surestime légèrement sur 2005–2018 et le sous-estime légèrement à partir de 2019.
- L'écart très élevé sur `M` s'explique en grande partie par la faible proportion initiale de mâles matures (2,96 %), qui rend ce compartiment très sensible aux erreurs relatives. `JF` est surestimé de façon structurelle.

### 5.2 Impact du taux d'abattage des femelles (2000–2020)

Effectif total simulé, en millions de têtes, tous les autres paramètres étant fixés à leur valeur de référence :

| δF | 2000 | 2010 | 2020 | Tendance |
|---|---|---|---|---|
| 0,05 | 4,542 | 7,279 | 11,851 | Croissance forte |
| 0,10 | 4,542 | 5,888 | 7,520 | Croissance modérée |
| 0,15 | 4,542 | 4,794 | 4,801 | Quasi-stagnation |
| 0,20 | 4,542 | 3,930 | 3,082 | Déclin modéré |
| 0,25 | 4,542 | 3,244 | 1,988 | Déclin marqué |
| 0,30 | 4,542 | 2,696 | 1,289 | Déclin sévère |
| 0,50 | 4,542 | 1,382 | 0,245 | Effondrement |

**Enseignement central** : le modèle met en évidence un **seuil critique de δF entre 0,15 et 0,20**. En deçà, le cheptel croît ou se stabilise ; au-delà, il décline. Le rapport en déduit qu'une régulation de l'abattage des femelles, notamment lors de la Tabaski, devrait maintenir δF sous ce seuil.

## 6. Prérequis et exécution

### Prérequis

- Python 3 (le notebook référence un environnement Anaconda en Python 3.10).
- Bibliothèques : `pandas`, `numpy`, `matplotlib`, `openpyxl`.
- `tkinter` (fourni avec la plupart des distributions Python) pour le simulateur interactif.

```bash
pip install pandas numpy matplotlib openpyxl
```

### Ordre d'exécution

Placer le dossier `Projet_CS_Ovins_Groupe_5` sur le **Bureau** ou dans **Documents** (ou lancer les scripts depuis ce dossier). Les scripts détectent automatiquement la racine du projet grâce à son nom, puis créent `data/` et `outputs/` si nécessaire.

| Étape | Script | Rôle | Sortie |
|---|---|---|---|
| 1 | `Préparation.py` | Charge `base_ovins_complete.xlsx`, définit les libellés | `data/base_ovins_nettoyee.xlsx` |
| 2 | `Affichage de l'évolution de la population.py` | Graphiques descriptifs | `graphique1` à `graphique4` |
| 3 | `Resolution par la méthode Runge-Kutta d'ordre 4.py` | RK4, validation, scénarios δF | `graphique_Ca_…`, `graphique_Cb_…` |
| 4 | `API.py` | Simulateur interactif | Exports à la demande |

```bash
cd Projet_CS_Ovins_Groupe_5/script
python "Préparation.py"
python "Affichage de l'évolution de la population.py"
python "Resolution par la méthode Runge-Kutta d'ordre 4.py"
```

## 7. Simulateur interactif

`API.py` propose une application Tkinter (*Simulateur de Cheptel Ovin — Sénégal*) qui permet de :

- faire varier **δF** de 0,01 à 0,50 avec un curseur et relancer la simulation RK4 ;
- afficher ou masquer chaque compartiment et l'effectif total ;
- comparer simulation et données réelles, avec un **audit par année** (estimé, réel, écart relatif) ;
- analyser l'**évolution temporelle des écarts** par catégorie sur une période choisie ;
- exporter les graphiques en PNG et les tableaux d'audit en Excel.

## 8. Sorties produites

| Fichier (`outputs/`) | Contenu | Script |
|---|---|---|
| `graphique1_effectif_total.png` | Évolution de l'effectif total (2000–2024) | Affichage |
| `graphique2_classes_age.png` | Répartition par classes d'âge | Affichage |
| `graphique3_compartiments.png` | Évolution des compartiments | Affichage |
| `graphique4_abattages.png` | Têtes abattues | Affichage |
| `graphique_Ca_modele_vs_reel.png` | Modèle RK4 vs données réelles (6 panneaux) | Résolution RK4 |
| `graphique_Cb_variation_abattage.png` | Effectif total selon δF (2000–2020) | Résolution RK4 |
| `graphique4_naissances_abattages.png`, `graphique_Ca_calibre.png` | Versions antérieures, non régénérées par les scripts fournis | — |

## 9. Limites et points d'attention

**Limites méthodologiques**

- **Paramètres incertains** : sept paramètres sont des proxys et cinq sont fixés de manière arbitraire, faute de sources. Une collecte auprès de l'ISRA/LNERV ou du MEPA permettrait de les calibrer plus rigoureusement.
- **Paramètres constants** sur 24 ans : le modèle ne capture pas l'accélération de la croissance observée après 2019, ni les chocs climatiques ou sanitaires (par ex. le fléchissement vers 2014).
- **Compartiments mal ajustés** : `M`, `JF`, `Fp` et `F` affichent des écarts élevés ; l'effectif total est le meilleur indicateur d'adéquation.
- **Seuil δF** : le seuil critique (0,15–0,20) dépend des paramètres arbitraires, en particulier `k` et `τ`, et doit être lu comme un ordre de grandeur.
- **Intégration** : le script de référence utilise un schéma RK4 à pas fixe sans estimation d'erreur ; l'écart relatif du script ajoute 1 au dénominateur pour éviter une division par zéro, ce qui diffère légèrement de la formule du rapport.

**Points techniques à corriger avant diffusion**

- `API.py` lit `chemin_data` sans le définir : lancé seul, le simulateur affiche une erreur « fichier introuvable ». Il faut y ajouter la détection de la racine du projet, comme dans `Préparation.py`.
- `script.py` contient un chemin absolu propre à une machine (`C:/Users/DELL/…`) ; utiliser plutôt `Préparation.py`.
- `notebook.ipynb` ne contient que la configuration des chemins et cherche un dossier `code/` alors que le dossier s'appelle `script/`.
- Le fichier temporaire `data/~$base_ovins_nettoyee.xlsx` (verrou Excel) est à supprimer.

## 10. Sources

- FAOSTAT (FAO, 2024) : effectifs du cheptel ovin du Sénégal, 2000–2024.
- ANSD (2018-2019). *Recensement National de l'Agriculture (RNA)*.
- Buldgen A., Dieng A. et al. *Productivité des élevages villageois de moutons du bassin arachidier sénégalais*. FAO/INDR Thiès. https://www.fao.org/4/u7600t/u7600T0d.htm
- Hamadou O. et al. (2021). *Paramètres démographiques des troupeaux ovins Peulhs*.
- Clément V. et al. (1997). Variabilité des caractères de reproduction chez les petits ruminants en milieu traditionnel au Sénégal. *Rev. Élev. Méd. Vét. Pays Trop.*, 50(3), 235–249.
- Akpo Y. et al. Études sur le mouton nain d'Afrique de l'Ouest : incidence de la mortalité périnatale au Nigeria. *Rev. Élev. Méd. Vét. Pays Trop.* doi:10.19182/remvt.9222
- Ministère de l'Élevage et des Productions Animales (MEPA, 2022).

La liste détaillée figure dans le rapport et dans le fichier `data/Parametre_repartition de la population en catégorie.xlsx`.

## 11. Citation

```
THIOUB, C., NGAKE YAMAHA, H. P., NDIAYE, C. M. M. & KEITA, L. (2026). Évolution du bétail
en Afrique de l'Ouest : le cas des petits ruminants (ovins) au Sénégal. Projet de Calcul
Scientifique, ENSAE Pierre Ndiaye, Dakar. Sous la supervision de M. Omar DIOP.
```

*Licence : à préciser par les auteurs avant toute diffusion publique.*
