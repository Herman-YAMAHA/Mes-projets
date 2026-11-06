# TP6 Google Earth Engine - Python : Groupe 1
Analyse spatiale par indices spectraux au Sénégal (2018)

**Auteurs** : Gerald ADDJITA, David Landry AGNANGMA SANAM, Marème DIOP, Herman Parfait NGAKE YAMAHA, Cheikh THIOUB

**Encadreur** : M. Aboubacar HEMA
Année académique : 2025–2026

**Note importante** : Les bases contenant les données EHCVM 2018 et les indicateurs calculés pour ce TP se trouvent dans le dossier "EHCVM_INDICATEURS" disponible via le lien suivant : https://drive.google.com/drive/folders/1scoPr4DSIRbMACKRDTKH0T2pMqjvrLYo?usp=sharing.

## Présentation générale du projet

Ce projet collectif vise à analyser plusieurs dimensions environnementales et territoriales du Sénégal à partir d’indices spectraux calculés à partir des images Sentinel-2, traitées avec Google Earth Engine via l’API Python.

L’étude est réalisée à l’échelle des 45 départements pour l’année 2018. Les indicateurs produits ont vocation à être intégrés et combinés avec les données socio-économiques issues de l’enquête EHCVM, dans une perspective d’analyse conjointe environnement – conditions de vie.

Chaque membre du groupe est responsable d’un indice spectral spécifique, avec une méthodologie propre, intégrée dans un cadre méthodologique commun.

## Structure globale du projet

```
TP6_GR1_ADDJITA_AGNANGMA_DIOP_NGAKE_THIOUB/
│
├── outputs/                     # Résultats et sorties des analyses
│
├── scripts/                     # Notebooks Jupyter des analyses
│   ├── TP6_SES_Groupe_1_BAI     # Analyse BAI (Burn Area Index)
│   ├── TP6_SES_Groupe_1_BSI     # Analyse BSI (Bare Soil Index)
│   ├── TP6_SES_Groupe_1_NDBI    # Analyse NDBI (Normalized Difference Built-up Index)
│   ├── TP6_SES_Groupe_1_NDTI    # Analyse NDTI (Normalized Difference Turbidity Index)
│   └── TP6_SES_Groupe_1_NDVI    # Analyse NDVI (Normalized Difference Vegetation Index)
│
└── README                       # Documentation du projet
```


## Objectifs généraux

- Exploiter la télédétection pour produire des indicateurs environnementaux robustes  
- Analyser les disparités spatiales à l’échelle départementale  
- Produire des cartes et indicateurs spatialisés exploitables  
- Enrichir les bases EHCVM avec des variables environnementales  

## Données communes au projet

### Imagerie satellitaire

- Satellite : Sentinel-2 (Copernicus)  
- Collection : COPERNICUS/S2_SR_HARMONIZED  
- Niveau : réflectance de surface (SR)  
- Période : 1er janvier – 31 décembre 2018  
- Résolution spatiale : 10 à 20 mètres  
- Prétraitement : correction atmosphérique et masquage des nuages  

### Limites administratives

- Source : GADM  
- Niveaux :
  - Niveau 0 : Sénégal
  - Niveau 2 : 45 départements
- Projection : WGS84 (EPSG:4326)

### Données socio-économiques

- Enquête EHCVM 2018
  - Base individu
  - Base welfare
- Variables clés : grappe, ménage, département

## Indicateur 1 — NDTI : turbidité des eaux

### Objectif spécifique

Évaluer et cartographier la turbidité des eaux de surface afin d’identifier les zones à risque environnemental et les priorités de gestion hydrique.

### Définition de l’indice

Le Normalized Difference Turbidity Index permet d’estimer la concentration en matières en suspension dans l’eau.

Formule :

NDTI = (Rouge − Vert) / (Rouge + Vert)

- Rouge : bande 4 (665 nm)  
- Vert : bande 3 (560 nm)  

### Fondement physique

Les eaux turbides présentent une réflectance plus élevée dans le rouge du fait de la diffusion par les particules en suspension, contrairement aux eaux claires.

### Interprétation des valeurs

| Valeur NDTI | Classe | Interprétation |
|------------|-------|----------------|
| > 0,3 | Eau très turbide | Forte charge sédimentaire |
| 0,1 – 0,3 | Eau turbide | Qualité dégradée |
| -0,1 – 0,1 | Eau modérément claire | Qualité acceptable |
| -0,3 – -0,1 | Eau claire | Bonne qualité |
| < -0,3 | Non-eau ou végétation | Hors périmètre hydrique |

### Méthodologie spécifique

- Sélection des images Sentinel-2 pour l’année 2018  
- Prétraitement et masquage des nuages  
- Calcul du NDTI pixel par pixel  
- Calcul de la moyenne annuelle  
- Agrégation des valeurs à l’échelle départementale  
- Visualisation cartographique  

### Sorties

- Carte de la turbidité des eaux  
- Valeur moyenne du NDTI par département  

## Indicateur 2 — NDVI : végétation et biomasse

### Contexte

Dans un pays où l’agriculture et le pastoralisme occupent une place centrale, le NDVI permet d’évaluer la vigueur de la végétation et les contrastes agro-écologiques.

### Formule

NDVI = (B8 − B4) / (B8 + B4)

- B8 : proche infrarouge (NIR)  
- B4 : rouge  

### Méthodologie spécifique

1. Masquage des nuages  
   Basé sur la bande SCL :
   - Pixels conservés : végétation, sol nu, eau, nuages fins, ombres
   - Pixels exclus : nuages opaques, pixels saturés ou défectueux

2. Calcul du NDVI par image  
   Ajout d’une bande NDVI à chaque image Sentinel-2.

3. Moyenne temporelle annuelle  
   Calcul de la moyenne du NDVI sur l’ensemble de l’année 2018.

4. Agrégation départementale  
   Utilisation de reduceRegions avec la moyenne comme statistique.

5. Moyenne nationale  
   Calculée directement sur la mosaïque NDVI finale.

6. Harmonisation des noms administratifs  
   Corrections manuelles pour assurer la cohérence avec les bases EHCVM.

7. Intégration aux bases EHCVM  
   Ajout du NDVI moyen par département aux bases individu et welfare.

### Sorties

- Carte NDVI  
- Tableau NDVI par département  
- Bases EHCVM enrichies  

## Indicateur 3 — NDBI : urbanisation

### Objectif

Mesurer l’intensité de l’urbanisation et des surfaces bâties à l’échelle départementale.

### Définition de l’indice

Le Normalized Difference Built-up Index permet d’identifier les zones artificialisées.

Formule :

NDBI = (B11 − B8) / (B11 + B8)

- B11 : infrarouge à ondes courtes (SWIR)  
- B8 : proche infrarouge (NIR)  

### Méthodologie spécifique

- Sélection des images Sentinel-2 SR pour 2018  
- Masquage basé sur la bande SCL :
  - Conservation : végétation, eau, nuages fins
  - Exclusion : nuages opaques, pixels défectueux, ombres et sols nus
- Calcul du NDBI pixel par pixel  
- Moyenne annuelle  
- Agrégation par département  

### Visualisation et restitution

- Carte de l’urbanisation  
- Choroplèthe départementale  
- Graphiques de comparaison et analyse de régression  

## Indicateur 4 — BAI : zones brûlées

### Objectif

Analyser et quantifier les zones brûlées au Sénégal à l’échelle départementale pour l’année 2018 afin de soutenir la gestion environnementale et agricole.

### Méthodologie spécifique

- Préparation des shapefiles départementaux  
- Conversion en FeatureCollection GEE  
- Filtrage spatial et temporel des images Sentinel-2  
- Calcul du BAI à partir des bandes rouge et NIR  
- Application d’un masque distinguant végétation, sols nus brûlés, eau et zones urbaines  
- Agrégation par département  
- Analyse statistique et visualisation  

### Interprétation du BAI moyen

| BAI moyen | Interprétation |
|----------|----------------|
| < 10 | Non brûlé |
| 10 – 50 | Végétation sèche |
| 50 – 150 | Zones brûlées probables |
| > 150 | Brûlé |

Cette interprétation est proposée par l’auteur en raison d’une littérature limitée sur les seuils standards du BAI.

### Sorties

- Tableau BAI par département  
- Fichier CSV exportable  
- Statistiques descriptives et graphiques  

## Indicateur 5 — BSI : sol nu

### Objectif

Identifier et caractériser les surfaces minérales en les distinguant de la végétation et des plans d’eau.

### Définition et fondement physique

Le sol nu présente une réflectance élevée dans le rouge et le SWIR, et plus faible dans le bleu et le NIR. Le BSI exploite cette opposition spectrale pour discriminer les surfaces.

### Formule

BSI = [(SWIR + R) − (NIR + B)] / [(SWIR + R) + (NIR + B)]

### Méthodologie spécifique

- Sélection des images Sentinel-2 pour 2018  
- Prétraitement et masquage des pixels non valides  
- Calcul du BSI pixel par pixel  
- Moyenne annuelle  
- Agrégation à l’échelle départementale  
- Fusion avec les bases EHCVM  

### Analyse spatiale attendue

- Valeurs plus faibles au sud, zones plus humides et végétalisées  
- Valeurs plus élevées au nord et à l’est, zones plus sèches et sableuses  

### Limites

Le BSI ne permet pas de distinguer parfaitement les sols nus naturels des surfaces artificialisées. L’interprétation doit être complétée par d’autres indices ou données d’occupation du sol.

### Sorties

- Valeur moyenne annuelle du BSI par département  
- Bases EHCVM enrichies  



## Limites globales du projet

Malgré l’intérêt des résultats obtenus, ce projet présente plusieurs limites qu’il convient de souligner pour une interprétation rigoureuse des indicateurs.

 Limites liées aux données satellitaires  
Les images Sentinel-2, bien que de haute résolution spatiale, restent sensibles à la couverture nuageuse, particulièrement durant la saison des pluies. Malgré les procédures de masquage, certains pixels résiduels peuvent affecter les moyennes annuelles des indices, en particulier pour les zones humides et forestières.

 Limites méthodologiques des indices spectraux  
Les indices spectraux utilisés reposent sur des signatures spectrales simplifiées et peuvent présenter des confusions entre certaines classes. Par exemple, les surfaces urbaines peuvent être confondues avec des sols nus pour le BSI, ou certaines zones sèches avec des zones brûlées pour le BAI. L’utilisation d’un indice isolé ne permet donc pas une discrimination parfaite des types de surfaces.

.

## Conclusion

Ce projet met en œuvre une approche intégrée combinant télédétection, analyse spatiale et données socio-économiques.  
La séparation méthodologique par indicateur garantit la rigueur scientifique, tandis que l’intégration finale permet une lecture multidimensionnelle du territoire sénégalais.
