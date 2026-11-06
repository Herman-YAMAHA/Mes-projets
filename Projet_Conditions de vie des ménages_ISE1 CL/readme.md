# Impact des transferts monétaires sur la pauvreté et les inégalités au Sénégal

**Simulation de sept scénarios de transferts à partir de l'EHCVM 2018, vieillie à 2025**

Projet d'analyse de la pauvreté — ISE1 CL, ENSAE Pierre Ndiaye (Dakar) — Année académique 2025–2026

| | |
|---|---|
| **Auteur** | Herman Parfait NGAKE YAMAHA, élève en ISE1-CL à l'ENSAE |
| **Superviseur** | M. Omar SENE, spécialiste des politiques publiques et analyste de données |
| **Outil** | Stata (script `.do`) |
| **Données** | Enquête harmonisée sur les conditions de vie des ménages (EHCVM) 2018/2019, Sénégal |
| **Langue du rapport** | Anglais |

---

## Table des matières

1. [Contexte et objectif](#1-contexte-et-objectif)
2. [Contenu du dépôt](#2-contenu-du-dépôt)
3. [Méthodologie](#3-méthodologie)
4. [Scénarios simulés](#4-scénarios-simulés)
5. [Principaux résultats](#5-principaux-résultats)
6. [Prérequis et exécution](#6-prérequis-et-exécution)
7. [Sorties produites](#7-sorties-produites)
8. [Limites et points d'attention](#8-limites-et-points-dattention)
9. [Sources et références](#9-sources-et-références)
10. [Citation](#10-citation)

---

## 1. Contexte et objectif

Les programmes de transferts monétaires occupent une place croissante dans les politiques de protection sociale en Afrique subsaharienne. Au Sénégal, la pauvreté monétaire reste élevée et fortement polarisée entre milieux urbain et rural.

Ce projet répond à la question suivante :

> **Dans quelle mesure des politiques de transferts monétaires, selon leurs modalités de ciblage, peuvent-elles réduire la pauvreté et les inégalités au Sénégal en 2025 ?**

Pour cela, la base EHCVM 2018 est « vieillie » afin de refléter les conditions économiques et démographiques de 2025. Sept scénarios de transferts sont ensuite simulés. Leur coût budgétaire, leur impact sur la pauvreté (indices FGT) et sur les inégalités (coefficient de Gini) et leur efficience sont comparés.

## 2. Contenu du dépôt

```
Projet_Conditions de vie des ménages/
├── Do_file_Herman_Parfait_NGAKE_YAMAHA.do   
├── Report_Herman_Parfait_NGAKE_YAMAHA.pdf   
└── readme_md.md                                # Ce document
```

Le rapport contient l'introduction, la description des politiques et l'analyse budgétaire, la méthodologie, l'analyse des résultats, les recommandations de politique économique, la conclusion et les références.

## 3. Méthodologie

Le script est structuré en huit sections numérotées (0 à 7), abondamment commentées.

| Section | Contenu |
|---|---|
| **0** | Création automatique de l'arborescence de travail (dossier racine et `outputs/`) |
| **1** | Chargement de la base ménage (`welfare`) depuis un dépôt GitHub public |
| **2** | **Vieillissement des données 2018 → 2025** |
| **3** | Indices de pauvreté FGT (α = 0, 1, 2) pour 2018 et 2025 |
| **4** | Coefficient de Gini (courbe de Lorenz discrète, règle des trapèzes) |
| **5** | **Simulation des 7 scénarios** : fusion avec la base individu, éligibilité, coûts, FGT, efficience, désagrégation urbain/rural, Gini |
| **6** | Export des résultats vers Excel (6 onglets) |
| **7** | Export de 9 graphiques PNG |

### 3.1 Vieillissement des données

Trois ajustements sont appliqués successivement :

| Variable | Ajustement | Ratio |
|---|---|---|
| Poids de sondage | `hhweight_2025 = hhweight × Pop₂₀₂₅ / Pop₂₀₁₈` | 1,213 (15 726 037 → 19 075 962 hab.) |
| Dépenses totales | `dtot_2025 = dtot × PIB/hab₂₀₂₅ / PIB/hab₂₀₁₈` | 1,317 (1 459 → 1 921 USD courants) |
| Seuil de pauvreté | `zref_2025 = zref × IHPC₂₀₂₅ / IHPC₂₀₁₈` | 1,258 (81,31 → 102,25 ; base 2023 = 100) |

Les dépenses par tête sont recalculées avec les déflateurs spatial et temporel d'origine, conservés pour préserver les disparités structurelles de l'enquête :

```
pcexp_2025 = dtot_2025 / (hhsize × def_spa × def_temp)
```

### 3.2 Indices de pauvreté (Foster–Greer–Thorbecke, 1984)

```
FGT(α) = (1/N) × Σ wᵢ × ((z − yᵢ) / z)^α × 1(yᵢ < z)       avec wᵢ = hhweight × hhsize
```

- **FGT0** : incidence (taux de pauvreté)
- **FGT1** : profondeur (écart de pauvreté)
- **FGT2** : sévérité

### 3.3 Coefficient de Gini

Calculé à partir de la courbe de Lorenz discrète (ménages triés par dépense par tête croissante) :

```
Gini = 1 − Σ (Lₖ + Lₖ₋₁) × (Fₖ − Fₖ₋₁)
```

### 3.4 Simulation et efficience

Pour chaque scénario *s*, un transfert annuel uniforme de **200 000 FCFA** est ajouté à la dépense totale des ménages éligibles :

```
pcexp_s = (dtot_2025 + 200 000 × 1[éligible_s]) / (hhsize × def_spa × def_temp)
```

- **Coût** = 200 000 × nombre pondéré de ménages éligibles (`hhweight_2025`), exprimé aussi en % du PIB 2025.
- **Efficience** = `(FGT1_baseline − FGT1_scénario) / Coût_scénario`.

## 4. Scénarios simulés

| N° | Scénario | Critère d'éligibilité |
|---|---|---|
| S1 | Transfert universel | Tous les ménages |
| S2 | Transfert universel rural | Ménages en milieu rural |
| S3 | Ménages avec nourrisson | Au moins un enfant de moins d'un an |
| S4 | Ménages ruraux avec nourrisson | Critère S3 et résidence rurale |
| S5 | Ménages avec personne âgée | Au moins un membre de plus de 65 ans |
| S6 | Ménages avec membre handicapé | Au moins un membre avec un handicap permanent |
| S7 | Ménages pauvres | Dépense par tête 2025 inférieure au seuil 2025 |

Les critères démographiques (S3 à S6) proviennent de la base individu, agrégée au niveau ménage (`collapse (max)`).

## 5. Principaux résultats

> Les chiffres ci-dessous sont ceux du rapport (`Report_…pdf`).

### 5.1 Situation de référence : 2018 vs 2025

| Indicateur | 2018 | 2025 | Variation |
|---|---|---|---|
| FGT0, incidence (%) | 37,78 | 34,56 | −3,22 pts |
| FGT1, profondeur (%) | 10,30 | 9,10 | −1,19 pts |
| FGT2, sévérité (%) | 3,93 | 3,38 | −0,55 pts |
| Coefficient de Gini | 0,3510 | 0,3506 | −0,0004 |
| Seuil de pauvreté (FCFA/an) | 333 441 | 419 312 | +85 871 |

En 2025, le taux de pauvreté atteint **50,26 % en milieu rural** contre **16,72 % en milieu urbain**.

### 5.2 Comparaison des scénarios (classés par efficience)

| Rang | Scénario | Coût (Mds FCFA) | ΔFGT1 (pts) |
|---|---|---|---|
| 1 | S7, Ménages pauvres | 106,6 | −1,29 |
| 2 | S4, Ruraux avec nourrisson | 57,2 | −0,36 |
| 3 | S2, Universel rural | 202,3 | −1,02 |
| 4 | S3, Avec nourrisson | 98,4 | −0,45 |
| 5 | S6, Avec membre handicapé | 104,1 | −0,36 |
| 6 | S5, Avec personne âgée | 130,1 | −0,44 |
| 7 | S1, Universel | 434,7 | −1,29 |

### 5.3 Enseignements clés

- **Le ciblage des ménages pauvres (S7) égale l'impact du transfert universel (S1)** sur les trois indices FGT (FGT0 : 34,56 % → 31,57 %), pour **0,51 % du PIB contre 2,10 %**, soit un coût environ quatre fois moindre.
- Les scénarios démographiques (S3, S5, S6) réduisent le taux de pauvreté de **moins d'un point**.
- Tous les scénarios réduisent le Gini, mais **modestement** (de −0,002 à −0,009 au niveau national). S7 est le plus efficace (0,351 → 0,342).
- La pauvreté est **concentrée en milieu rural** : S1, S2 et S7 produisent des effets identiques en zone rurale (FGT0 : 50,26 % → 46,10 %).
- Les hypothèses de vieillissement pèsent lourdement : la hausse des prix (IHPC) relève le seuil de pauvreté et absorbe une partie de la croissance du PIB par habitant.

## 6. Prérequis et exécution

### Prérequis

- **Stata**, version récente. Le script utilise `putexcel` avec options de mise en forme et `graph export`.
- **Connexion Internet** : les bases brutes sont chargées à la volée via `webuse` depuis le dépôt GitHub public `Shelvid-F/demo_poverty_hhcondition` :
  - `data/raw/ehcvm_welfare_SEN2018.dta` (base ménage)
  - `data/raw/ehcvm_individu_SEN2018.dta` (base individu)
- **Système Windows** avec disque `C:` accessible en écriture (voir ci-dessous).
- Aucun package externe n'est installé par le script.

### Exécution

1. Ouvrir Stata.
2. Exécuter le script :
   ```stata
   do "Do_file_Herman_Parfait_NGAKE_YAMAHA.do"
   ```
3. Le script crée automatiquement `C:/Herman_Parfait_NGAKE_YAMAHA/` et son sous-dossier `outputs/`, puis y enregistre tous les résultats.

> **Pour changer le dossier de sortie**, modifier la ligne `local projet_dir "C:/Herman_Parfait_NGAKE_YAMAHA"` (section 0).

### Analyse de sensibilité

Les hypothèses sont centralisées dans des scalaires, faciles à modifier :

| Scalaire | Rôle | Valeur par défaut |
|---|---|---|
| `transfert` | Montant annuel par ménage éligible (section 5.1) | 200 000 FCFA |
| `pop_2018`, `pop_2025` | Population (poids) | 15 726 037 / 19 075 962 |
| `gdppc_2018`, `gdppc_2025` | PIB par habitant (dépenses) | 1 459 / 1 921 USD |
| `ihpc_2018`, `ihpc_2025` | Indice des prix (seuil de pauvreté) | 81,31 / 102,25 |
| `taux_change`, `pib_2025_usd` | Conversion du PIB en FCFA | 563 / 36 839 000 000 |

## 7. Sorties produites

Dans `C:/Herman_Parfait_NGAKE_YAMAHA/outputs/` :

```
outputs/
├── results.xlsx                          # 6 onglets (voir ci-dessous)
├── graph1a_cost_ranking_absolute.png     # Coûts en milliards de FCFA
├── graph1b_cost_ranking_pctgdp.png       # Coûts en % du PIB
├── graph2_fgt0_before_after.png          # FGT0 avant/après transfert
├── graph3_fgt1_before_after.png          # FGT1 avant/après transfert
├── graph4_fgt2_before_after.png          # FGT2 avant/après transfert
├── graph5_efficiency_ranking.png         # Classement par efficience
├── graph6_gini_before_after.png          # Gini avant/après transfert
├── graph7_fgt_evolution_2018_2025.png    # FGT 2018 vs 2025
└── graph8_gini_evolution_2018_2025.png   # Gini 2018 vs 2025
```

**Onglets de `results.xlsx`** : `FGT & Gini Baseline`, `Cost of Scenarios`, `FGT Impact by Scenario`, `Efficiency Ranking`, `FGT Urban-Rural`, `Gini by Scenario`.

Les fichiers temporaires `_welfare_temp.dta` et `_eligibilite_temp.dta` sont supprimés en fin de section 5.

## 8. Limites et points d'attention

- **Vieillissement simplifié** : les dépenses sont revalorisées uniformément avec la croissance du PIB/hab en USD courants, et les poids avec la croissance démographique globale. Aucune dynamique différenciée (régions, quintiles, composition des ménages) n'est modélisée.
- **Coûts administratifs exclus** : le coût de ciblage (registre social, mise à jour, identification) n'est pas intégré, ce qui peut réduire l'avantage apparent de S7.
- **Statique** : pas d'effets de second tour (consommation locale, prix, comportements d'offre de travail).
- **Sources externes** : PIB/hab et PIB (Worldometer) et IHPC (ANSD/DMIS) sont saisis manuellement dans le script ; leur mise à jour doit être faite dans la section 2.1.
- **Portabilité** : chemin d'écriture fixé sur `C:` (Windows) et dépendance à un dépôt GitHub tiers pour les données.
- **Interprétation du Gini rural** : le Gini rural (0,273), inférieur au Gini urbain (0,351), reflète une distribution plus homogène dans un contexte de pauvreté généralisée, et non une plus grande équité.

## 9. Sources et références

- Foster, J., Greer, J. & Thorbecke, E. (1984). *A class of decomposable poverty measures*. Econometrica, 52(3), 761–766.
- ANSD (2019). *Enquête Harmonisée sur les Conditions de Vie des Ménages (EHCVM) 2018/2019*. Dakar.
- ANSD / DMIS (2025). *Indice harmonisé des prix à la consommation, évolutions 2018–2025, base 2023*. Dakar.
- Commission de l'UEMOA (2019). *Guide méthodologique de l'EHCVM*. Ouagadougou.
- République du Sénégal (2023). *RGPH-5, résultats préliminaires*. Dakar : ANSD.
- Worldometer (2025). *Senegal GDP per Capita 2018–2025*. https://www.worldometers.info/gdp/senegal-gdp/
- Banque mondiale (2023). *Poverty and Shared Prosperity 2022: Correcting Course*. Washington, DC.

La liste complète figure dans le rapport PDF.

## 10. Citation

```
NGAKE YAMAHA, H. P. (2026). Assessing the impact of cash transfers on poverty and
inequality in Senegal. Projet ISE1-CL, ENSAE Pierre Ndiaye, Dakar.
Sous la supervision de M. Omar SENE.
```

## Contact

Herman Parfait NGAKE YAMAHA — ISE1-CL, ENSAE Pierre Ndiaye, Dakar.

*Licence : à préciser par l'auteur avant toute diffusion publique.*
