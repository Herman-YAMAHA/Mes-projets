/*===========================================================================
   PROJET ISE1 CL 2026 - Analyse de la Pauvreté au Sénégal
   
   Auteur      : Herman Parfait NGAKE YAMAHA, élève en ISE1-CL à l'ENSAE
   
   Superviseur : M. Omar SENE, spécialiste des politiques publiques et analyste 
   de données
   
   Description : Script complet — Vieillissement des données EHCVM 2018,
                 calcul des indicateurs de pauvreté et d'inégalité,
                 simulation des scénarios de transferts monétaires,
                 et export des résultats (Excel + graphiques PNG).

   Portabilité :
     Ce script ne contient aucun chemin absolu propre à une machine.
     À l'exécution, il crée automatiquement sur le disque C: le dossier
       C:/Herman_Parfait_NGAKE_YAMAHA/
     ainsi que le sous-dossier outputs/ qui contiendra tous les résultats.
     Ce comportement est identique quel que soit l'ordinateur utilisé,
     à condition que le disque C: soit accessible en écriture.
===========================================================================*/

clear all      // Efface toutes les données en mémoire
set more off   // Désactive la pause automatique dans la fenêtre de résultats


/*===========================================================================
   SECTION 0 : CRÉATION AUTOMATIQUE DU DOSSIER DE TRAVAIL SUR LE DISQUE C:
   -------------------------------------------------------------------------
   On définit le nom du dossier racine du projet directement sur C:, ce qui
   garantit que le script fonctionne de la même façon sur n'importe quel
   ordinateur Windows, sans avoir à modifier le chemin.

   La commande `capture mkdir` crée le dossier s'il n'existe pas encore.
   Si le dossier existe déjà, elle ne produit aucune erreur (capture absorbe
   le code de retour non nul de mkdir).

   Arborescence créée :
     C:/Herman_Parfait_NGAKE_YAMAHA/
     └── outputs/           ← tous les fichiers de sortie (Excel + PNG)
===========================================================================*/

* Définition du chemin racine sur C: (aucune modification nécessaire)
local projet_dir "C:/Herman_Parfait_NGAKE_YAMAHA"

* Création du dossier racine s'il n'existe pas encore
capture mkdir "`projet_dir'"

* Création du sous-dossier outputs/ s'il n'existe pas encore
capture mkdir "`projet_dir'/outputs"

* Positionnement du répertoire de travail sur le dossier racine du projet
* Toutes les références relatives (outputs/...) partiront de là
cd "`projet_dir'"

* Affichage du répertoire de travail actif pour confirmation visuelle
display " "
display "======================================================="
display "RÉPERTOIRE DE TRAVAIL : `projet_dir'"
display "Les sorties seront enregistrées dans : `projet_dir'/outputs/"
display "======================================================="

* Définition du chemin du fichier Excel de sortie (chemin relatif)
local output_file "outputs/results.xlsx"


/*===========================================================================
   SECTION 1 : CHARGEMENT DES DONNÉES
   -------------------------------------------------------------------------
   Les deux fichiers de l'EHCVM 2018 (Sénégal) sont chargés depuis un
   dépôt GitHub public :
   
     - ehcvm_welfare_SEN2018.dta  : base ménage (welfare)
       → contient les dépenses, le seuil de pauvreté, les déflateurs,
         le milieu de résidence (urbain/rural), les poids de sondage.
		 
     - ehcvm_individu_SEN2018.dta : base individu
       → contient l'âge et le statut de handicap de chaque membre,
         nécessaires pour définir les critères d'éligibilité démographiques.
		 
   On commence par la base welfare. La base individu sera chargée plus tard
   dans la section 5 (fusion pour les critères d'éligibilité).
===========================================================================*/

* Déclaration du dépôt GitHub hébergeant les données brutes
webuse set "https://raw.githubusercontent.com/Shelvid-F/demo_poverty_hhcondition/main"

* Chargement de la base welfare (niveau ménage)
webuse "data/raw/ehcvm_welfare_SEN2018.dta", clear


/*===========================================================================
   SECTION 2 : VIEILLISSEMENT DES DONNÉES (2018 → 2025)
   -------------------------------------------------------------------------
   Objectif : simuler les conditions économiques et démographiques de 2025
              à partir de l'enquête EHCVM 2018.
   Trois dimensions sont ajustées :
     1. Les poids de sondage           → reflètent la croissance démographique
     2. Les dépenses de consommation   → reflètent la croissance du PIB/habitant
     3. Le seuil de pauvreté           → reflète l'évolution des prix (IHPC)
===========================================================================*/

/*---------------------------------------------------------------------------
   2.1 : Définition des paramètres de vieillissement sous forme de scalaires
   -------------------------------------------------------------------------
   L'utilisation de scalaires présente deux avantages :
     - Les hypothèses sont centralisées en un seul endroit → facile à modifier
     - Les scalaires sont réutilisables dans tout le script sans répétition

   Sources :
     Population : Recensements RGPHAE 2013 et RGPH-5 2023 (projections ANSD)
     PIB/hab    : Worldometer (USD courants)
     IHPC       : ANSD/DMIS — fichier IHPC_base_2023_Evolutions_DMIS.xlsx
---------------------------------------------------------------------------*/

* --- Paramètres démographiques ---
scalar pop_2018   = 15726037   // Population du Sénégal en 2018
scalar pop_2025   = 19075962   // Population du Sénégal en 2025
scalar ratio_pop  = pop_2025 / pop_2018
// ratio_pop mesure la croissance démographique entre les deux dates ;
// il sera appliqué aux poids de sondage pour ramener la représentativité à 2025

* --- Paramètres économiques (PIB par habitant) ---
scalar gdppc_2018  = 1459      // PIB par habitant 2018 (USD courants)
scalar gdppc_2025  = 1921      // PIB par habitant 2025 (USD courants)
scalar ratio_gdppc = gdppc_2025 / gdppc_2018
// ratio_gdppc mesure la croissance du niveau de vie moyen ;
// il sera appliqué aux dépenses totales des ménages

* --- Paramètres de prix (IHPC, base 2023) ---
scalar ihpc_2018  = 81.31      // IHPC global au Sénégal en 2018 (base 2023 = 100)
scalar ihpc_2025  = 102.25     // IHPC global au Sénégal en 2025 (base 2023 = 100)
scalar ratio_ihpc = ihpc_2025 / ihpc_2018
// ratio_ihpc mesure l'évolution des prix entre 2018 et 2025 ;
// il sera appliqué au seuil de pauvreté pour l'exprimer en FCFA de 2025

* --- Affichage des ratios calculés pour vérification ---
display "============================================"
display "RATIOS DE VIEILLISSEMENT"
display "============================================"
display "Ratio population   (poids)    : " %8.6f ratio_pop
display "Ratio PIB/habitant (dépenses) : " %8.6f ratio_gdppc
display "Ratio IHPC         (seuil)    : " %8.6f ratio_ihpc
display "============================================"


/*---------------------------------------------------------------------------
   2.2 : Application des ratios aux variables de la base welfare
   -------------------------------------------------------------------------
   Chaque variable vieillie est créée comme une nouvelle variable pour
   préserver les valeurs 2018 d'origine (utiles pour la comparaison).
---------------------------------------------------------------------------*/

* Poids de sondage 2025 : poids 2018 × ratio de croissance démographique
gen hhweight_2025 = hhweight * ratio_pop
label variable hhweight_2025 "Pondération ménage estimée en 2025"

* Dépenses totales 2025 : dépenses 2018 × ratio de croissance du PIB/hab
gen dtot_2025 = dtot * ratio_gdppc
label variable dtot_2025 "Dépenses totales annuelles estimées en 2025 (FCFA)"

* Dépenses par tête 2025 :
* Les déflateurs spatiaux (def_spa) et temporels (def_temp) de 2018 sont
* conservés tels quels car ils reflètent les disparités structurelles
* intra-enquête (régions, saisons).
gen pcexp_2025 = dtot_2025 / (hhsize * def_spa * def_temp)
label variable pcexp_2025 "Dépenses par tête estimées en 2025 (FCFA)"

* Seuil de pauvreté 2025 : seuil 2018 × ratio d'évolution des prix (IHPC)
* Cette actualisation garantit que le seuil reflète le coût réel de la vie en 2025
gen zref_2025 = zref * ratio_ihpc
label variable zref_2025 "Seuil de pauvreté estimé en 2025 (FCFA)"


/*---------------------------------------------------------------------------
   2.3 : Vérification des variables vieillies
   -------------------------------------------------------------------------
   On compare les statistiques descriptives 2018 et 2025 pour s'assurer
   que les ajustements ont bien été appliqués dans le bon sens.
   Le seuil de pauvreté est affiché pour vérification directe.
---------------------------------------------------------------------------*/

display " "
display "============================================"
display "VÉRIFICATION DES VARIABLES VIEILLIES"
display "============================================"
summarize hhweight hhweight_2025    // hhweight_2025 doit être en moyenne plus grand
summarize dtot dtot_2025            // dtot_2025 > dtot (croissance économique)
summarize pcexp pcexp_2025          // pcexp_2025 > pcexp 
summarize zref zref_2025            // zref_2025 > zref (inflation)
display " "
display "Seuil de pauvreté 2018 : " zref[1]      " FCFA"
display "Seuil de pauvreté 2025 : " zref_2025[1] " FCFA"


/*===========================================================================
   SECTION 3 : CALCUL DES INDICES FGT
   -------------------------------------------------------------------------
   Formule générale (Foster, Greer & Thorbecke, 1984) :
     FGT(α) = (1/N) × Σ [ wᵢ × ((z − yᵢ)/z)^α × 1(yᵢ < z) ]
   où :
     α = 0 → Incidence de la pauvreté (headcount ratio P0)
     α = 1 → Profondeur de la pauvreté (poverty gap P1)
     α = 2 → Sévérité de la pauvreté  (squared poverty gap P2)
     wᵢ = hhweight × hhsize  : poids individuel (ménage × taille)
     z  = seuil de pauvreté
     yᵢ = dépenses par tête du ménage i

   Note sur la pondération :
     La formule originale suppose un poids uniforme 1/N. Ici on pondère par
     wᵢ = hhweight × hhsize pour tenir compte du plan de sondage de l'EHCVM :
     hhweight représente combien de ménages de la population chaque ménage
     enquêté représente, et hhsize ramène au niveau individuel.
===========================================================================*/

/*---------------------------------------------------------------------------
   3.1 : FGT 2018 (données brutes de l'enquête, non vieillies)
   -------------------------------------------------------------------------
   On utilise pcexp et zref (valeurs 2018 originales).
---------------------------------------------------------------------------*/

* Indicatrice de pauvreté : vaut 1 si le ménage est pauvre, 0 sinon
gen pauvre_2018 = (pcexp < zref)
label variable pauvre_2018 "Indicatrice de pauvreté 2018 (pcexp < zref)"

* Écart normalisé au seuil (poverty gap ratio) :
* = (z − y)/z si pauvre, = 0 sinon
* Mesure à quelle fraction du seuil se trouve le ménage pauvre en dessous
gen gap_2018 = ((zref - pcexp) / zref) * pauvre_2018
label variable gap_2018 "Écart normalisé au seuil de pauvreté 2018"

* Carré de l'écart normalisé : pénalise davantage les ménages les plus pauvres
* (mesure la sévérité ou dispersion de la pauvreté)
gen severity_2018 = gap_2018^2
label variable severity_2018 "Carré de l'écart normalisé 2018 (sévérité)"

* FGT0 : moyenne pondérée de l'indicatrice de pauvreté → taux de pauvreté
summarize pauvre_2018   [iw = hhweight * hhsize]
scalar fgt0_2018 = r(mean)

* FGT1 : moyenne pondérée de l'écart normalisé → profondeur de pauvreté
summarize gap_2018      [iw = hhweight * hhsize]
scalar fgt1_2018 = r(mean)

* FGT2 : moyenne pondérée du carré de l'écart → sévérité de pauvreté
summarize severity_2018 [iw = hhweight * hhsize]
scalar fgt2_2018 = r(mean)

display " "
display "============================================"
display "FGT 2018"
display "============================================"
display "FGT0 - Incidence  : " %6.4f fgt0_2018*100 " %"
display "FGT1 - Profondeur : " %6.4f fgt1_2018*100 " %"
display "FGT2 - Sévérité   : " %6.4f fgt2_2018*100 " %"
display "============================================"


/*---------------------------------------------------------------------------
   3.2 : FGT 2025 (données vieillies)
   -------------------------------------------------------------------------
   Même logique que pour 2018, en utilisant pcexp_2025 et zref_2025.
   Les poids sont hhweight_2025 × hhsize.
---------------------------------------------------------------------------*/

* Indicatrice de pauvreté 2025
gen pauvre_2025 = (pcexp_2025 < zref_2025)
label variable pauvre_2025 "Indicatrice de pauvreté 2025 (pcexp_2025 < zref_2025)"

* Écart normalisé 2025
gen gap_2025 = ((zref_2025 - pcexp_2025) / zref_2025) * pauvre_2025
label variable gap_2025 "Écart normalisé au seuil de pauvreté 2025"

* Carré de l'écart normalisé 2025
gen severity_2025 = gap_2025^2
label variable severity_2025 "Carré de l'écart normalisé 2025 (sévérité)"

* Calcul des FGT 2025 pondérés par hhweight_2025 × hhsize
summarize pauvre_2025   [iw = hhweight_2025 * hhsize]
scalar fgt0_2025 = r(mean)

summarize gap_2025      [iw = hhweight_2025 * hhsize]
scalar fgt1_2025 = r(mean)

summarize severity_2025 [iw = hhweight_2025 * hhsize]
scalar fgt2_2025 = r(mean)

display " "
display "============================================"
display "FGT 2025"
display "============================================"
display "FGT0 - Incidence  : " %6.4f fgt0_2025*100 " %"
display "FGT1 - Profondeur : " %6.4f fgt1_2025*100 " %"
display "FGT2 - Sévérité   : " %6.4f fgt2_2025*100 " %"
display "============================================"


/*---------------------------------------------------------------------------
   3.3 : Comparaison 2018 vs 2025
---------------------------------------------------------------------------*/

display " "
display "============================================"
display "COMPARAISON FGT 2018 vs 2025"
display "============================================"
display "           2018      2025    Variation"
display "FGT0 : " %6.2f fgt0_2018*100 "%   " %6.2f fgt0_2025*100 "%   " %6.2f (fgt0_2025-fgt0_2018)*100 " pts"
display "FGT1 : " %6.2f fgt1_2018*100 "%   " %6.2f fgt1_2025*100 "%   " %6.2f (fgt1_2025-fgt1_2018)*100 " pts"
display "FGT2 : " %6.2f fgt2_2018*100 "%   " %6.2f fgt2_2025*100 "%   " %6.2f (fgt2_2025-fgt2_2018)*100 " pts"
display "============================================"


/*===========================================================================
   SECTION 4 : CALCUL DU COEFFICIENT DE GINI
   -------------------------------------------------------------------------
   Méthode : Courbe de Lorenz discrète + Règle des trapèzes
   Formule : Gini = 1 − Σ [ (Lₖ + Lₖ₋₁) × (Fₖ − Fₖ₋₁) ]
   où :
     Fₖ = part cumulée de la population triée par revenus croissants
     Lₖ = part cumulée des dépenses correspondante

   Principe :
     - On trie les ménages du plus pauvre au plus riche (pcexp croissant)
     - On calcule les sommes cumulées pondérées de la population et des dépenses
     - On normalise pour obtenir des proportions entre 0 et 1 (courbe de Lorenz)
     - On approche l'aire sous la courbe de Lorenz par la somme des trapèzes
     - Gini = 1 − 2 × (aire sous la courbe de Lorenz)
       car l'aire du triangle de parfaite égalité = 0,5
===========================================================================*/

/*---------------------------------------------------------------------------
   4.1 : Gini 2018
---------------------------------------------------------------------------*/

* Tri indispensable : les sommes cumulées n'ont de sens que si les ménages
* sont ordonnés du plus pauvre au plus riche
sort pcexp

* Poids individuel 2018 : nombre d'individus représentés par ce ménage dans la pop.
gen wi_2018 = hhweight * hhsize
label variable wi_2018 "Poids individuel 2018 (hhweight * hhsize)"

* Somme cumulée du poids population (axe X de la courbe de Lorenz)
gen cum_pop_2018 = sum(wi_2018)
* Somme cumulée des dépenses pondérées (axe Y de la courbe de Lorenz)
gen cum_dep_2018 = sum(wi_2018 * pcexp)
label variable cum_pop_2018 "Poids population cumulé 2018"
label variable cum_dep_2018 "Dépenses pondérées cumulées 2018"

* Récupération des totaux (valeurs maximales des sommes cumulées)
* pour pouvoir normaliser entre 0 et 1
summarize cum_pop_2018
scalar total_pop_2018 = r(max)
summarize cum_dep_2018
scalar total_dep_2018 = r(max)

* Normalisation → proportions entre 0 et 1
gen F_2018 = cum_pop_2018 / total_pop_2018   // Part cumulée de population
gen L_2018 = cum_dep_2018 / total_dep_2018   // Part cumulée de dépenses
label variable F_2018 "Part cumulée population 2018 (axe X Lorenz)"
label variable L_2018 "Part cumulée dépenses 2018   (axe Y Lorenz)"

* Valeurs décalées d'une observation (k−1) pour la formule des trapèzes
* À la première observation, le trapèze démarre à (0, 0)
gen F_lag_2018 = F_2018[_n-1]
gen L_lag_2018 = L_2018[_n-1]
replace F_lag_2018 = 0 in 1   // Point d'origine de la courbe de Lorenz
replace L_lag_2018 = 0 in 1

* Aire de chaque trapèze élémentaire sous la courbe de Lorenz :
*   base × hauteur moyenne = (Fₖ − Fₖ₋₁) × (Lₖ + Lₖ₋₁) / 2
gen trapeze_2018 = (L_2018 + L_lag_2018) * (F_2018 - F_lag_2018) / 2

* Aire totale sous la courbe de Lorenz = somme de tous les trapèzes
summarize trapeze_2018
scalar aire_lorenz_2018 = r(sum)

* Gini = 1 − 2 × aire sous la Lorenz
* (l'aire du triangle de parfaite égalité vaut 0,5, d'où la formule simplifiée)
scalar gini_2018 = 1 - 2 * aire_lorenz_2018

display " "
display "============================================"
display "GINI 2018"
display "============================================"
display "Coefficient de Gini 2018 : " %6.4f gini_2018
display "============================================"


/*---------------------------------------------------------------------------
   4.2 : Gini 2025 (même méthode, variables vieillies)
   -------------------------------------------------------------------------
   On répète exactement la même procédure avec pcexp_2025 et hhweight_2025.
---------------------------------------------------------------------------*/

* Tri par dépenses par tête vieillies croissantes
sort pcexp_2025

* Poids individuel 2025
gen wi_2025 = hhweight_2025 * hhsize
label variable wi_2025 "Poids individuel 2025 (hhweight_2025 * hhsize)"

* Sommes cumulées pondérées
gen cum_pop_2025 = sum(wi_2025)
gen cum_dep_2025 = sum(wi_2025 * pcexp_2025)
label variable cum_pop_2025 "Poids population cumulé 2025"
label variable cum_dep_2025 "Dépenses pondérées cumulées 2025"

* Totaux pour normalisation
summarize cum_pop_2025
scalar total_pop_2025 = r(max)
summarize cum_dep_2025
scalar total_dep_2025 = r(max)

* Courbe de Lorenz 2025
gen F_2025 = cum_pop_2025 / total_pop_2025
gen L_2025 = cum_dep_2025 / total_dep_2025
label variable F_2025 "Part cumulée population 2025 (axe X Lorenz)"
label variable L_2025 "Part cumulée dépenses 2025   (axe Y Lorenz)"

* Valeurs décalées d'une observation
gen F_lag_2025 = F_2025[_n-1]
gen L_lag_2025 = L_2025[_n-1]
replace F_lag_2025 = 0 in 1
replace L_lag_2025 = 0 in 1

* Aire sous la courbe de Lorenz 2025
gen trapeze_2025 = (L_2025 + L_lag_2025) * (F_2025 - F_lag_2025) / 2
summarize trapeze_2025
scalar aire_lorenz_2025 = r(sum)

* Gini 2025
scalar gini_2025 = 1 - 2 * aire_lorenz_2025

display " "
display "============================================"
display "GINI 2025"
display "============================================"
display "Coefficient de Gini 2025 : " %6.4f gini_2025
display "============================================"


/*---------------------------------------------------------------------------
   4.3 : Comparaison Gini 2018 vs 2025
---------------------------------------------------------------------------*/

display " "
display "============================================"
display "COMPARAISON GINI 2018 vs 2025"
display "============================================"
display "Gini 2018 : " %6.4f gini_2018
display "Gini 2025 : " %6.4f gini_2025
display "Variation : " %6.4f (gini_2025 - gini_2018)
display "============================================"


/*===========================================================================
   SECTION 5 : SIMULATION DES SCÉNARIOS DE TRANSFERTS MONÉTAIRES
   -------------------------------------------------------------------------
   On simule 7 scénarios distincts de politiques de transferts.
   Pour chaque scénario, on recalcule les dépenses par tête post-transfert
   en ajoutant le montant du transfert aux ménages éligibles, puis on
   recalcule les indices FGT et le Gini sur la nouvelle distribution.
===========================================================================*/

/*---------------------------------------------------------------------------
   5.1 : Paramètre du transfert annuel par ménage éligible
   -------------------------------------------------------------------------
   Centraliser ce montant dans un scalaire permet de faire des analyses
   de sensibilité (ex : 100 000 FCFA, 300 000 FCFA) en ne modifiant qu'ici.
---------------------------------------------------------------------------*/

scalar transfert = 200000   // Transfert annuel par ménage éligible (FCFA)
display " "
display "Montant du transfert annuel par ménage éligible : " transfert " FCFA"


/*---------------------------------------------------------------------------
   5.2 : Fusion welfare × individu pour les critères d'éligibilité
   -------------------------------------------------------------------------
   Trois scénarios (S3, S4, S5, S6) nécessitent de connaître la composition
   démographique du ménage (présence de nourrisson, personne âgée, handicapé).
   Ces informations se trouvent dans la base individu (une ligne par personne).

   Stratégie en 4 étapes :
     1. Sauvegarder la base welfare complète en fichier temporaire
     2. Charger la base individu et créer des indicateurs binaires par individu
     3. Agréger au niveau ménage avec collapse(max) : le résultat vaut 1
        si au moins un membre du ménage satisfait la condition
     4. Recharger welfare et fusionner (merge 1:1 sur hhid)

   Les fichiers temporaires (_welfare_temp.dta, _eligibilite_temp.dta) sont
   supprimés à la fin de la section (sous-section 5.9).
---------------------------------------------------------------------------*/

* Étape 1 : Sauvegarde de la base welfare en fichier temporaire
* (avec toutes les variables vieillies déjà créées en sections 2-4)
save "_welfare_temp.dta", replace

* Étape 2 : Chargement de la base individu depuis GitHub
webuse "data/raw/ehcvm_individu_SEN2018.dta", clear

* Création des indicateurs binaires au niveau individuel :
gen baby       = (age < 1)      // = 1 si la personne est un nourrisson (moins d'1 an)
gen elder      = (age > 65)     // = 1 si la personne a plus de 65 ans
gen handig_ind = (handig == 1)  // = 1 si la personne a un handicap permanent

* Étape 3 : Agrégation au niveau ménage par identifiant hhid
* collapse(max) donne 1 si AU MOINS UN membre satisfait la condition
collapse (max) has_baby   = baby       ///
               has_elder  = elder      ///
               has_handig = handig_ind ///
               , by(hhid)

label variable has_baby   "Ménage avec au moins un nourrisson (age < 1)"
label variable has_elder  "Ménage avec au moins une personne âgée (age > 65)"
label variable has_handig "Ménage avec au moins un membre handicapé (handig=1)"

* Sauvegarde de la table d'éligibilité (une ligne par ménage)
save "_eligibilite_temp.dta", replace

* Étape 4 : Rechargement de welfare et fusion avec les critères d'éligibilité
use "_welfare_temp.dta", clear
* merge 1:1 : chaque hhid est unique dans les deux bases
* nogenerate : on ne crée pas la variable _merge (inutile ici)
merge 1:1 hhid using "_eligibilite_temp.dta", nogenerate

* Vérification post-merge : fréquences des indicateurs d'éligibilité
display " "
display "============================================"
display "VÉRIFICATION DU MERGE WELFARE + INDIVIDU"
display "============================================"
tab has_baby    // Fréquences ménages avec nourrisson
tab has_elder   // Fréquences ménages avec personne âgée
tab has_handig  // Fréquences ménages avec membre handicapé
display "============================================"


/*---------------------------------------------------------------------------
   5.3 : Définition des critères d'éligibilité pour chaque scénario
   -------------------------------------------------------------------------
   Pour chaque scénario s (1 à 7), on crée une variable binaire elig_s? :
     = 1 si le ménage est éligible au transfert dans ce scénario
     = 0 sinon
---------------------------------------------------------------------------*/

* S1 : Transfert universel — tous les ménages sans exception
gen elig_s1 = 1
label variable elig_s1 "Sc1 : Tous les ménages"

* S2 : Transfert universel rural — uniquement les ménages en zone rurale
* La variable milieu prend la valeur 2 pour le milieu rural dans l'EHCVM
gen elig_s2 = (milieu == 2)
label variable elig_s2 "Sc2 : Ménages ruraux (milieu=2)"

* S3 : Ménages avec au moins un nourrisson (enfant de moins d'un an)
gen elig_s3 = has_baby
label variable elig_s3 "Sc3 : Ménages avec nourrisson"

* S4 : Ménages ruraux avec au moins un nourrisson (double critère géo + démo)
gen elig_s4 = (has_baby == 1 & milieu == 2)
label variable elig_s4 "Sc4 : Ménages ruraux avec nourrisson"

* S5 : Ménages avec au moins une personne de plus de 65 ans
gen elig_s5 = has_elder
label variable elig_s5 "Sc5 : Ménages avec personne âgée (>65)"

* S6 : Ménages avec au moins un membre en situation de handicap permanent
gen elig_s6 = has_handig
label variable elig_s6 "Sc6 : Ménages avec membre handicapé"

* S7 : Ménages dont la dépense par tête 2025 est inférieure au seuil 2025
* (ménages pauvres au sens monétaire en 2025)
gen elig_s7 = pauvre_2025
label variable elig_s7 "Sc7 : Ménages pauvres 2025"

* Vérification : nombre de ménages éligibles par scénario (non pondéré)
display " "
display "============================================"
display "MÉNAGES ÉLIGIBLES PAR SCÉNARIO (échantillon brut)"
display "============================================"
foreach s in 1 2 3 4 5 6 7 {
    count if elig_s`s' == 1
    display "Scénario `s' : " r(N) " ménages éligibles"
}
display "============================================"


/*---------------------------------------------------------------------------
   5.4 : Calcul du coût de chaque scénario
   -------------------------------------------------------------------------
   Le transfert est versé au ménage (et non par individu), donc on pondère
   uniquement par hhweight_2025 (et non hhweight_2025 × hhsize).

   Coût total du scénario s :
     Coût_s = transfert × Σ (hhweight_2025 × elig_s?)

   Le PIB 2025 en FCFA est calculé à partir du PIB en USD × taux de change
   fixe UEMOA (1 USD = 563 FCFA), afin d'exprimer les coûts en % du PIB.
---------------------------------------------------------------------------*/

* PIB 2025 en FCFA (conversion depuis USD via le taux de change fixe UEMOA)
scalar taux_change    = 563.00         // Taux fixe : 1 USD = 563 FCFA
scalar pib_2025_usd   = 36839000000    // PIB Sénégal 2025 en USD (Worldometer)
scalar pib_2025_fcfa  = pib_2025_usd * taux_change

display " "
display "PIB Sénégal 2025 : " %25.0f pib_2025_fcfa " FCFA"

* Calcul du coût de chaque scénario et de sa part dans le PIB
display " "
display "============================================"
display "COÛT DES SCÉNARIOS"
display "============================================"
display "Scénario | Coût total (FCFA)     | % PIB"
display "---------|----------------------|-------"

foreach s in 1 2 3 4 5 6 7 {

    * Nombre pondéré de ménages éligibles dans la population 2025
    * iw = hhweight_2025 (poids ménage uniquement, pas × hhsize)
    summarize elig_s`s' [iw = hhweight_2025]
    scalar nb_menages_s`s' = r(sum)   // Nb total de ménages éligibles (représentatif)

    * Coût total = montant annuel × nombre de ménages éligibles pondéré
    scalar cout_s`s' = transfert * nb_menages_s`s'

    * Part du coût total dans le PIB 2025 (en pourcentage)
    scalar pct_pib_s`s' = (cout_s`s' / pib_2025_fcfa) * 100

    display "Scénario `s' | " %20.0f cout_s`s' " | " %6.4f pct_pib_s`s' " %"
}
display "============================================"


/*---------------------------------------------------------------------------
   5.5 : Impact des scénarios sur les indices FGT
   -------------------------------------------------------------------------
   Pour chaque scénario s :
     1. Calcul des dépenses par tête post-transfert :
          pcexp_s? = (dtot_2025 + transfert × elig_s?) / (hhsize × def_spa × def_temp)
        → Les ménages éligibles voient leurs dépenses augmenter du montant du transfert
        → Les ménages non éligibles conservent leurs dépenses inchangées
     2. Recalcul des indicateurs FGT sur la nouvelle distribution
     3. Calcul de l'efficacité = réduction de FGT1 / coût total du scénario
        → Plus cette valeur est élevée, plus le scénario est efficient budgétairement
---------------------------------------------------------------------------*/

display " "
display "========================================================================"
display "IMPACT DES SCÉNARIOS SUR LES FGT (baseline 2025)"
display "========================================================================"
display "Scénario | FGT0_base | FGT0_end | FGT1_base | FGT1_end | FGT2_base | FGT2_end | Efficacité"

foreach s in 1 2 3 4 5 6 7 {

    * Dépenses par tête post-transfert pour le scénario s :
    * Le transfert est ajouté aux dépenses totales du ménage (dtot_2025),
    * puis on redivise par la taille et les déflateurs pour revenir au niveau individuel
    gen pcexp_s`s' = (dtot_2025 + transfert * elig_s`s') / ///
                     (hhsize * def_spa * def_temp)
    label variable pcexp_s`s' "Dépenses par tête post-transfert scénario `s'"

    * Indicatrice de pauvreté post-transfert :
    * un ménage peut sortir de la pauvreté si le transfert le fait dépasser le seuil
    gen pauvre_s`s' = (pcexp_s`s' < zref_2025)

    * Écart normalisé post-transfert (nul pour les ménages non pauvres)
    gen gap_s`s' = ((zref_2025 - pcexp_s`s') / zref_2025) * pauvre_s`s'

    * Carré de l'écart normalisé post-transfert (mesure la sévérité)
    gen severity_s`s' = gap_s`s'^2

    * Calcul des FGT post-transfert pondérés par poids individuel 2025
    summarize pauvre_s`s'   [iw = hhweight_2025 * hhsize]
    scalar fgt0_s`s' = r(mean)

    summarize gap_s`s'      [iw = hhweight_2025 * hhsize]
    scalar fgt1_s`s' = r(mean)

    summarize severity_s`s' [iw = hhweight_2025 * hhsize]
    scalar fgt2_s`s' = r(mean)

    * Efficacité = réduction de la profondeur de pauvreté (FGT1) par FCFA dépensé
    scalar efficacite_s`s' = (fgt1_2025 - fgt1_s`s') / cout_s`s'

    display "Scénario `s' | " ///
        %6.2f fgt0_2025*100    "%  | " ///
        %6.2f fgt0_s`s'*100   "% | " ///
        %6.2f fgt1_2025*100    "%  | " ///
        %6.2f fgt1_s`s'*100   "% | " ///
        %6.2f fgt2_2025*100    "%  | " ///
        %6.2f fgt2_s`s'*100   "% | " ///
        %12.4e efficacite_s`s'
}
display "========================================================================"


/*---------------------------------------------------------------------------
   5.6 : Désagrégation des FGT par milieu de résidence (Urbain / Rural)
   -------------------------------------------------------------------------
   On recalcule les FGT post-transfert séparément pour les ménages urbains
   (milieu = 1) et ruraux (milieu = 2) en ajoutant la condition "if".
   Cela permet de mesurer les disparités géographiques de l'impact des transferts.
---------------------------------------------------------------------------*/

display " "
display "========================================================================"
display "FGT PAR MILIEU (URBAIN / RURAL) - POST-TRANSFERT"
display "========================================================================"

foreach milieu_val in 1 2 {

    * Étiquette lisible pour les affichages dans la fenêtre de résultats
    if `milieu_val' == 1 local milieu_label "Urbain"
    if `milieu_val' == 2 local milieu_label "Rural"

    display " "
    display "--- Milieu : `milieu_label' ---"
    display "Scénario | FGT0     | FGT1     | FGT2"

    foreach s in 1 2 3 4 5 6 7 {

        * FGT0 post-transfert restreint au milieu concerné
        summarize pauvre_s`s' [iw = hhweight_2025 * hhsize] ///
            if milieu == `milieu_val'
        scalar fgt0_s`s'_`milieu_val' = r(mean)

        * FGT1 post-transfert pour ce milieu
        summarize gap_s`s' [iw = hhweight_2025 * hhsize] ///
            if milieu == `milieu_val'
        scalar fgt1_s`s'_`milieu_val' = r(mean)

        * FGT2 post-transfert pour ce milieu
        summarize severity_s`s' [iw = hhweight_2025 * hhsize] ///
            if milieu == `milieu_val'
        scalar fgt2_s`s'_`milieu_val' = r(mean)

        display "Scénario `s' | " ///
            %6.2f fgt0_s`s'_`milieu_val'*100 "% | " ///
            %6.2f fgt1_s`s'_`milieu_val'*100 "% | " ///
            %6.2f fgt2_s`s'_`milieu_val'*100 "%"
    }
}

* Calcul des FGT baseline 2025 par milieu (avant tout transfert)
* Ces scalaires serviront à remplir les colonnes "Base" de l'onglet FGT Urban-Rural
foreach milieu_val in 1 2 {
    summarize pauvre_2025   [iw = hhweight_2025 * hhsize] if milieu == `milieu_val'
    scalar fgt0_2025_`milieu_val' = r(mean)
    summarize gap_2025      [iw = hhweight_2025 * hhsize] if milieu == `milieu_val'
    scalar fgt1_2025_`milieu_val' = r(mean)
    summarize severity_2025 [iw = hhweight_2025 * hhsize] if milieu == `milieu_val'
    scalar fgt2_2025_`milieu_val' = r(mean)
}

display "========================================================================"


/*---------------------------------------------------------------------------
   5.7 : Impact des scénarios sur le Gini (niveau national)
   -------------------------------------------------------------------------
   On applique exactement la même méthode que pour le Gini baseline (section 4),
   mais en utilisant les dépenses post-transfert pcexp_s? à la place de pcexp_2025.
   Le tri par pcexp_s? croissant est refait pour chaque scénario.
---------------------------------------------------------------------------*/

display " "
display "========================================================================"
display "IMPACT DES SCÉNARIOS SUR LE GINI (national)"
display "========================================================================"
display "Scénario | Gini_baseline | Gini_endline | Variation"

foreach s in 1 2 3 4 5 6 7 {

    * Tri par dépenses post-transfert croissantes (obligatoire avant calcul Lorenz)
    sort pcexp_s`s'

    * Sommes cumulées pondérées pour la courbe de Lorenz post-transfert
    gen cum_pop_s`s' = sum(hhweight_2025 * hhsize)
    gen cum_dep_s`s' = sum(hhweight_2025 * hhsize * pcexp_s`s')

    * Totaux pour normalisation
    summarize cum_pop_s`s'
    scalar tot_pop_s`s' = r(max)
    summarize cum_dep_s`s'
    scalar tot_dep_s`s' = r(max)

    * Courbe de Lorenz normalisée post-transfert
    gen F_s`s' = cum_pop_s`s' / tot_pop_s`s'
    gen L_s`s' = cum_dep_s`s' / tot_dep_s`s'

    * Valeurs décalées d'une observation pour la règle des trapèzes
    gen F_lag_s`s' = F_s`s'[_n-1]
    gen L_lag_s`s' = L_s`s'[_n-1]
    replace F_lag_s`s' = 0 in 1
    replace L_lag_s`s' = 0 in 1

    * Calcul du Gini post-transfert via l'aire sous la courbe de Lorenz
    gen trap_s`s' = (L_s`s' + L_lag_s`s') * (F_s`s' - F_lag_s`s') / 2
    summarize trap_s`s'
    scalar gini_s`s' = 1 - 2 * r(sum)

    display "Scénario `s' | " ///
        %6.4f gini_2025    "        | " ///
        %6.4f gini_s`s'   "       | " ///
        %6.4f (gini_s`s' - gini_2025)
}
display "========================================================================"


/*---------------------------------------------------------------------------
   5.8 : Gini par milieu de résidence (Urbain / Rural)
   -------------------------------------------------------------------------
   IMPORTANT — Pourquoi on utilise preserve/restore ici et pas "if milieu==" :
     La règle des trapèzes suppose des sommes cumulées calculées sur des
     observations consécutives et triées de façon continue. Si on applique
     "if milieu==X" sur la base complète, les observations manquantes créent
     des discontinuités dans la courbe de Lorenz et produisent des valeurs
     de Gini incorrectes.
     Solution : on utilise preserve/restore pour isoler un sous-échantillon
     propre (uniquement les observations du milieu concerné) avant chaque calcul.
---------------------------------------------------------------------------*/

display " "
display "========================================================================"
display "GINI PAR MILIEU (URBAIN / RURAL)"
display "========================================================================"

foreach milieu_val in 1 2 {

    if `milieu_val' == 1 local milieu_label "Urbain"
    if `milieu_val' == 2 local milieu_label "Rural"

    display " "
    display "--- Milieu : `milieu_label' ---"
    display "Scénario | Gini_baseline | Gini_endline | Variation"

    * --- Gini baseline 2025 pour ce milieu ---
    preserve
        keep if milieu == `milieu_val'   // Restriction au sous-échantillon du milieu
        sort pcexp_2025                   // Tri croissant pour la courbe de Lorenz

        gen wi_base      = hhweight_2025 * hhsize
        gen cum_pop_base = sum(wi_base)
        gen cum_dep_base = sum(wi_base * pcexp_2025)

        summarize cum_pop_base
        scalar tot_pop_base_`milieu_val' = r(max)
        summarize cum_dep_base
        scalar tot_dep_base_`milieu_val' = r(max)

        gen F_base     = cum_pop_base / tot_pop_base_`milieu_val'
        gen L_base     = cum_dep_base / tot_dep_base_`milieu_val'
        gen F_lag_base = F_base[_n-1]
        gen L_lag_base = L_base[_n-1]
        replace F_lag_base = 0 in 1
        replace L_lag_base = 0 in 1

        gen trap_base = (L_base + L_lag_base) * (F_base - F_lag_base) / 2
        summarize trap_base
        scalar gini_base_`milieu_val' = 1 - 2 * r(sum)
    restore   // Restauration de la base complète après chaque bloc

    * --- Gini post-transfert pour chaque scénario et ce milieu ---
    foreach s in 1 2 3 4 5 6 7 {

        preserve
            keep if milieu == `milieu_val'   // Sous-échantillon propre
            sort pcexp_s`s'                   // Tri par dépenses post-transfert

            gen wi_s      = hhweight_2025 * hhsize
            gen cum_pop_s = sum(wi_s)
            gen cum_dep_s = sum(wi_s * pcexp_s`s')

            summarize cum_pop_s
            scalar tot_pop_ms = r(max)
            summarize cum_dep_s
            scalar tot_dep_ms = r(max)

            gen F_s     = cum_pop_s / tot_pop_ms
            gen L_s     = cum_dep_s / tot_dep_ms
            gen F_lag_s = F_s[_n-1]
            gen L_lag_s = L_s[_n-1]
            replace F_lag_s = 0 in 1
            replace L_lag_s = 0 in 1

            gen trap_s = (L_s + L_lag_s) * (F_s - F_lag_s) / 2
            summarize trap_s
            scalar gini_s`s'_`milieu_val' = 1 - 2 * r(sum)
        restore   // Restauration de la base complète

        display "Scénario `s' | " ///
            %6.4f gini_base_`milieu_val'                            "        | " ///
            %6.4f gini_s`s'_`milieu_val'                           "       | " ///
            %6.4f (gini_s`s'_`milieu_val' - gini_base_`milieu_val')
    }
}
display "========================================================================"


/*---------------------------------------------------------------------------
   5.9 : Nettoyage des fichiers temporaires
   -------------------------------------------------------------------------
   Les deux fichiers temporaires créés à l'étape 5.2 ont servi uniquement
   pour la fusion welfare × individu. On les supprime ici pour ne pas
   encombrer le répertoire de travail avec des fichiers parasites.
---------------------------------------------------------------------------*/

erase "_welfare_temp.dta"
erase "_eligibilite_temp.dta"


/*===========================================================================
   SECTION 6 : EXPORT DES RÉSULTATS VERS EXCEL
   -------------------------------------------------------------------------
   Tous les indicateurs calculés sont exportés dans le fichier Excel unique
   outputs/results.xlsx, organisé en 6 onglets thématiques.
   La commande putexcel permet d'écrire cellule par cellule avec mise en forme.
===========================================================================*/

/*---------------------------------------------------------------------------
   Labels des scénarios en anglais
   -------------------------------------------------------------------------
   Ces labels sont réutilisés dans tous les onglets Excel et dans les graphiques.
   Les définir ici comme locals évite toute répétition dans le code.
---------------------------------------------------------------------------*/

local lab1 "Universal Cash Transfer"
local lab2 "Rural Universal Cash Transfer"
local lab3 "Households with Infants (age < 1)"
local lab4 "Rural Households with Infants"
local lab5 "Households with Elderly (age > 65)"
local lab6 "Households with Disabled Member"
local lab7 "Poor Households (below poverty line)"


/*---------------------------------------------------------------------------
   ONGLET 1 : Indicateurs de pauvreté et d'inégalité — Baseline 2018 vs 2025
   -------------------------------------------------------------------------
   FGT0, FGT1, FGT2, Gini et seuil de pauvreté pour les deux dates,
   avant toute politique de transfert.
---------------------------------------------------------------------------*/

putexcel set "`output_file'", sheet("FGT & Gini Baseline") modify

putexcel A1 = "Poverty and Inequality Indicators - Baseline 2018 vs 2025", ///
    bold font("Calibri", 13)
putexcel A2 = "Source: EHCVM 2018 - Aged to 2025 | Author: Herman Parfait NGAKE YAMAHA"

putexcel A4 = "Indicator"   , bold border(bottom)
putexcel B4 = "2018"        , bold border(bottom)
putexcel C4 = "2025"        , bold border(bottom)
putexcel D4 = "Change"      , bold border(bottom)

* FGT0 : multiplié par 100 pour exprimer en pourcentage
putexcel A5 = "FGT0 - Headcount Ratio (%)"
putexcel B5 = (round(fgt0_2018*100, 0.01))
putexcel C5 = (round(fgt0_2025*100, 0.01))
putexcel D5 = (round((fgt0_2025 - fgt0_2018)*100, 0.01))

* FGT1 : profondeur de pauvreté en %
putexcel A6 = "FGT1 - Poverty Depth (%)"
putexcel B6 = (round(fgt1_2018*100, 0.01))
putexcel C6 = (round(fgt1_2025*100, 0.01))
putexcel D6 = (round((fgt1_2025 - fgt1_2018)*100, 0.01))

* FGT2 : sévérité de pauvreté en %
putexcel A7 = "FGT2 - Poverty Severity (%)"
putexcel B7 = (round(fgt2_2018*100, 0.01))
putexcel C7 = (round(fgt2_2025*100, 0.01))
putexcel D7 = (round((fgt2_2025 - fgt2_2018)*100, 0.01))

* Gini : indice entre 0 et 1, arrondi à 4 décimales
putexcel A8 = "Gini Coefficient"
putexcel B8 = (round(gini_2018, 0.0001))
putexcel C8 = (round(gini_2025, 0.0001))
putexcel D8 = (round(gini_2025 - gini_2018, 0.0001))

* Seuil de pauvreté : variation exprimée en FCFA (valeur absolue, pas en points)
putexcel A10 = "Poverty Line (FCFA/year)"  , bold
putexcel B10 = (round(zref[1], 1))
putexcel C10 = (round(zref_2025[1], 1))
putexcel D10 = (round(zref_2025[1] - zref[1], 1))

display "Sheet 1 (FGT & Gini Baseline) exported."


/*---------------------------------------------------------------------------
   ONGLET 2 : Coût des scénarios
   -------------------------------------------------------------------------
   Pour chaque scénario : nombre de ménages éligibles (pondéré, représentatif
   de la population 2025), coût total en FCFA, et part dans le PIB 2025.
---------------------------------------------------------------------------*/

putexcel set "`output_file'", sheet("Cost of Scenarios") modify

putexcel A1 = "Cost of Cash Transfer Scenarios - Senegal 2025", ///
    bold font("Calibri", 13)
putexcel A2 = "Annual transfer per eligible household: 200 000 FCFA"

putexcel A4 = "Scenario ID"              , bold border(bottom)
putexcel B4 = "Scenario Description"     , bold border(bottom)
putexcel C4 = "Eligible HH (weighted)"   , bold border(bottom)
putexcel D4 = "Total Cost (FCFA)"        , bold border(bottom)
putexcel E4 = "Cost (% of GDP)"          , bold border(bottom)

forvalues s = 1/7 {
    local row = `s' + 4
    putexcel A`row' = `s'
    putexcel B`row' = "`lab`s''"
    putexcel C`row' = (round(nb_menages_s`s', 1))
    putexcel D`row' = (round(cout_s`s', 1))
    putexcel E`row' = (round(pct_pib_s`s', 0.0001))
}

* Ligne de référence : PIB 2025 utilisé pour les calculs de part
putexcel A13 = "Reference GDP 2025 (FCFA)", bold
putexcel B13 = (round(pib_2025_fcfa, 1))

display "Sheet 2 (Cost of Scenarios) exported."


/*---------------------------------------------------------------------------
   ONGLET 3 : Impact des scénarios sur les FGT (niveau national)
   -------------------------------------------------------------------------
   Pour chaque scénario : FGT0, FGT1 et FGT2 avant et après transfert,
   et les variations correspondantes (Δ = endline − baseline).
---------------------------------------------------------------------------*/

putexcel set "`output_file'", sheet("FGT Impact by Scenario") modify

putexcel A1 = "FGT Indicators Before and After Cash Transfer - National Level", ///
    bold font("Calibri", 13)
putexcel A2 = "Baseline: 2025 aged data | Transfer: 200 000 FCFA per eligible household"

putexcel A4 = "Scenario"       , bold border(bottom)
putexcel B4 = "FGT0 Base (%)"  , bold border(bottom)
putexcel C4 = "FGT0 End (%)"   , bold border(bottom)
putexcel D4 = "ΔFGT0"          , bold border(bottom)
putexcel E4 = "FGT1 Base (%)"  , bold border(bottom)
putexcel F4 = "FGT1 End (%)"   , bold border(bottom)
putexcel G4 = "ΔFGT1"          , bold border(bottom)
putexcel H4 = "FGT2 Base (%)"  , bold border(bottom)
putexcel I4 = "FGT2 End (%)"   , bold border(bottom)
putexcel J4 = "ΔFGT2"          , bold border(bottom)

forvalues s = 1/7 {
    local row = `s' + 4
    putexcel A`row' = "`lab`s''"
    putexcel B`row' = (round(fgt0_2025*100,             0.01))
    putexcel C`row' = (round(fgt0_s`s'*100,             0.01))
    putexcel D`row' = (round((fgt0_s`s'-fgt0_2025)*100, 0.01))
    putexcel E`row' = (round(fgt1_2025*100,             0.01))
    putexcel F`row' = (round(fgt1_s`s'*100,             0.01))
    putexcel G`row' = (round((fgt1_s`s'-fgt1_2025)*100, 0.01))
    putexcel H`row' = (round(fgt2_2025*100,             0.01))
    putexcel I`row' = (round(fgt2_s`s'*100,             0.01))
    putexcel J`row' = (round((fgt2_s`s'-fgt2_2025)*100, 0.01))
}

display "Sheet 3 (FGT Impact by Scenario) exported."


/*---------------------------------------------------------------------------
   ONGLET 4 : Classement des scénarios par efficacité
   -------------------------------------------------------------------------
   Les scénarios sont triés par efficacité décroissante (gsort -eff) dans
   un dataset temporaire (preserve/restore), puis écrits avec leur rang.
   L'efficacité est conservée telle quelle (notation scientifique dans Excel).
---------------------------------------------------------------------------*/

putexcel set "`output_file'", sheet("Efficiency Ranking") modify

putexcel A1 = "Efficiency of Cash Transfer Scenarios", ///
    bold font("Calibri", 13)
putexcel A2 = "Efficiency = (FGT1 Baseline - FGT1 Endline) / Total Cost"

putexcel A4 = "Rank"                , bold border(bottom)
putexcel B4 = "Scenario"            , bold border(bottom)
putexcel C4 = "Total Cost (FCFA)"   , bold border(bottom)
putexcel D4 = "FGT1 Baseline (%)"   , bold border(bottom)
putexcel E4 = "FGT1 Endline (%)"    , bold border(bottom)
putexcel F4 = "ΔFGT1"               , bold border(bottom)
putexcel G4 = "Efficiency"          , bold border(bottom)

preserve
    * Construction d'un dataset temporaire à 7 observations (une par scénario)
    clear
    set obs 7
    gen s_id       = .
    gen cost       = .
    gen fgt1_b     = .
    gen fgt1_e     = .
    gen eff        = .
    gen str60 scenario = ""

    forvalues s = 1/7 {
        replace s_id   = `s'             in `s'
        replace cost   = cout_s`s'       in `s'
        replace fgt1_b = fgt1_2025       in `s'
        replace fgt1_e = fgt1_s`s'       in `s'
        replace eff    = efficacite_s`s' in `s'
    }

    replace scenario = "Universal Cash Transfer"               if s_id == 1
    replace scenario = "Rural Universal Cash Transfer"         if s_id == 2
    replace scenario = "Households with Infants (age < 1)"    if s_id == 3
    replace scenario = "Rural Households with Infants"        if s_id == 4
    replace scenario = "Households with Elderly (age > 65)"   if s_id == 5
    replace scenario = "Households with Disabled Member"      if s_id == 6
    replace scenario = "Poor Households (below poverty line)" if s_id == 7

    * Tri décroissant par efficacité → rang 1 = scénario le plus efficient
    gsort -eff
    gen rank = _n

    * Écriture dans l'onglet Excel ligne par ligne
    forvalues i = 1/7 {
        local row = `i' + 4
        local sc  = scenario[`i']
        local co  = cost[`i']
        local fb  = fgt1_b[`i']
        local fe  = fgt1_e[`i']
        local ef  = eff[`i']
        local rk  = rank[`i']

        putexcel A`row' = `rk'
        putexcel B`row' = "`sc'"
        putexcel C`row' = (`co')
        putexcel D`row' = (round(`fb'*100, 0.0001))
        putexcel E`row' = (round(`fe'*100, 0.0001))
        putexcel F`row' = (round((`fe'-`fb')*100, 0.0001))
        putexcel G`row' = (`ef')
    }
restore

display "Sheet 4 (Efficiency Ranking) exported."


/*---------------------------------------------------------------------------
   ONGLET 5 : FGT désagrégés par milieu de résidence (Urbain / Rural)
   -------------------------------------------------------------------------
   Deux blocs dans l'onglet (urbain puis rural), chacun avec les FGT0, FGT1
   et FGT2 baseline et endline pour chacun des 7 scénarios.
---------------------------------------------------------------------------*/

putexcel set "`output_file'", sheet("FGT Urban-Rural") modify

putexcel A1 = "FGT Indicators by Area of Residence - Before and After Transfer", ///
    bold font("Calibri", 13)
putexcel A2 = "Urban (milieu=1) vs Rural (milieu=2)"

* --- Bloc URBAN (lignes 4 à 12) ---
putexcel A4  = "URBAN"         , bold font("Calibri", 11)
putexcel A5  = "Scenario"      , bold border(bottom)
putexcel B5  = "FGT0 Base (%)" , bold border(bottom)
putexcel C5  = "FGT0 End (%)"  , bold border(bottom)
putexcel D5  = "FGT1 Base (%)" , bold border(bottom)
putexcel E5  = "FGT1 End (%)"  , bold border(bottom)
putexcel F5  = "FGT2 Base (%)" , bold border(bottom)
putexcel G5  = "FGT2 End (%)"  , bold border(bottom)

forvalues s = 1/7 {
    local row = `s' + 5
    putexcel A`row' = "`lab`s''"
    putexcel B`row' = (round(fgt0_2025_1*100, 0.01))   // FGT0 baseline urbain
    putexcel C`row' = (round(fgt0_s`s'_1*100, 0.01))   // FGT0 endline  urbain
    putexcel D`row' = (round(fgt1_2025_1*100, 0.01))
    putexcel E`row' = (round(fgt1_s`s'_1*100, 0.01))
    putexcel F`row' = (round(fgt2_2025_1*100, 0.01))
    putexcel G`row' = (round(fgt2_s`s'_1*100, 0.01))
}

* --- Bloc RURAL (lignes 14 à 22) ---
putexcel A14 = "RURAL"         , bold font("Calibri", 11)
putexcel A15 = "Scenario"      , bold border(bottom)
putexcel B15 = "FGT0 Base (%)" , bold border(bottom)
putexcel C15 = "FGT0 End (%)"  , bold border(bottom)
putexcel D15 = "FGT1 Base (%)" , bold border(bottom)
putexcel E15 = "FGT1 End (%)"  , bold border(bottom)
putexcel F15 = "FGT2 Base (%)" , bold border(bottom)
putexcel G15 = "FGT2 End (%)"  , bold border(bottom)

forvalues s = 1/7 {
    local row = `s' + 15
    putexcel A`row' = "`lab`s''"
    putexcel B`row' = (round(fgt0_2025_2*100, 0.01))   // FGT0 baseline rural
    putexcel C`row' = (round(fgt0_s`s'_2*100, 0.01))   // FGT0 endline  rural
    putexcel D`row' = (round(fgt1_2025_2*100, 0.01))
    putexcel E`row' = (round(fgt1_s`s'_2*100, 0.01))
    putexcel F`row' = (round(fgt2_2025_2*100, 0.01))
    putexcel G`row' = (round(fgt2_s`s'_2*100, 0.01))
}

display "Sheet 5 (FGT Urban-Rural) exported."


/*---------------------------------------------------------------------------
   ONGLET 6 : Coefficient de Gini par scénario et par milieu de résidence
   -------------------------------------------------------------------------
   Trois blocs : national, urbain, rural.
   Pour chaque scénario : Gini baseline, Gini endline, variation (Δ).
---------------------------------------------------------------------------*/

putexcel set "`output_file'", sheet("Gini by Scenario") modify

putexcel A1 = "Gini Coefficient by Scenario and Area of Residence", ///
    bold font("Calibri", 13)
putexcel A2 = "Baseline: 2025 aged data"

* --- Bloc NATIONAL (lignes 4 à 12) ---
putexcel A4  = "NATIONAL"      , bold font("Calibri", 11)
putexcel A5  = "Scenario"      , bold border(bottom)
putexcel B5  = "Gini Baseline" , bold border(bottom)
putexcel C5  = "Gini Endline"  , bold border(bottom)
putexcel D5  = "Variation"     , bold border(bottom)

forvalues s = 1/7 {
    local row = `s' + 5
    putexcel A`row' = "`lab`s''"
    putexcel B`row' = (round(gini_2025,           0.0001))   // Gini baseline 2025
    putexcel C`row' = (round(gini_s`s',           0.0001))   // Gini après transfert
    putexcel D`row' = (round(gini_s`s'-gini_2025, 0.0001))   // Δ (négatif = réduction)
}

* --- Bloc URBAN (lignes 14 à 22) ---
putexcel A14 = "URBAN"         , bold font("Calibri", 11)
putexcel A15 = "Scenario"      , bold border(bottom)
putexcel B15 = "Gini Baseline" , bold border(bottom)
putexcel C15 = "Gini Endline"  , bold border(bottom)
putexcel D15 = "Variation"     , bold border(bottom)

forvalues s = 1/7 {
    local row = `s' + 15
    putexcel A`row' = "`lab`s''"
    putexcel B`row' = (round(gini_base_1,                0.0001))
    putexcel C`row' = (round(gini_s`s'_1,                0.0001))
    putexcel D`row' = (round(gini_s`s'_1 - gini_base_1,  0.0001))
}

* --- Bloc RURAL (lignes 24 à 32) ---
putexcel A24 = "RURAL"         , bold font("Calibri", 11)
putexcel A25 = "Scenario"      , bold border(bottom)
putexcel B25 = "Gini Baseline" , bold border(bottom)
putexcel C25 = "Gini Endline"  , bold border(bottom)
putexcel D25 = "Variation"     , bold border(bottom)

forvalues s = 1/7 {
    local row = `s' + 25
    putexcel A`row' = "`lab`s''"
    putexcel B`row' = (round(gini_base_2,                0.0001))
    putexcel C`row' = (round(gini_s`s'_2,                0.0001))
    putexcel D`row' = (round(gini_s`s'_2 - gini_base_2,  0.0001))
}

display "Sheet 6 (Gini by Scenario) exported."


/*===========================================================================
   SECTION 7 : GRAPHIQUES
   -------------------------------------------------------------------------
   Neuf graphiques PNG sont exportés dans outputs/ :
     graph1a : Coûts absolus en milliards FCFA (barres horizontales)
     graph1b : Coûts en % du PIB (barres horizontales)
     graph2  : FGT0 avant/après par scénario (barres groupées)
     graph3  : FGT1 avant/après par scénario (barres groupées)
     graph4  : FGT2 avant/après par scénario (barres groupées)
     graph5  : Efficacité classée (barres horizontales)
     graph6  : Gini avant/après par scénario (barres groupées)
     graph7  : FGT 2018 vs 2025 baseline (barres groupées)
     graph8  : Gini 2018 vs 2025 baseline (barres simples)

   Convention commune à tous les graphiques :
     - preserve/restore : dataset temporaire à 7 obs. pour le graphe, puis retour
       à la base principale (évite de modifier les données en mémoire)
     - gsort -var : tri décroissant pour les graphes horizontaux (1a, 1b, 5)
     - bargap(20) : espace entre paires de barres dans les graphes groupés
     - blabel : valeurs affichées au-dessus ou à côté des barres
     - plotregion(margin) : espace supplémentaire pour les étiquettes de valeurs
     - width(1400) : résolution exportée en 1400 pixels de large
===========================================================================*/


/*---------------------------------------------------------------------------
   Graphique 1a : Coûts absolus classés du plus cher au moins cher
   -------------------------------------------------------------------------
   Les valeurs sont converties en milliards de FCFA (division par 10^9) pour
   la lisibilité. L'axe est horizontal (graph hbar) pour que les labels soient
   lisibles sans rotation.
---------------------------------------------------------------------------*/

preserve
    clear
    set obs 7
    gen cost_mrd = .        // Coût en milliards de FCFA
    gen str50 sc_label = ""

    forvalues s = 1/7 {
        replace cost_mrd = cout_s`s' / 1000000000 in `s'   // Conversion milliards
        replace sc_label = "`lab`s''"             in `s'
    }

    gsort -cost_mrd   // Tri décroissant : plus cher en haut de l'axe

    graph hbar cost_mrd,                                              ///
        over(sc_label, sort(cost_mrd) descending                      ///
            label(labsize(small) angle(0)))                           ///
        bar(1, color(navy))                                           ///
        blabel(bar, format(%6.2f) size(small) position(outside)       ///
            color(black))                                 ///
        title("Cost of Cash Transfer Scenarios",                      ///
            size(medium))                                             ///
        subtitle("Annual transfer: 200,000 FCFA per eligible household") ///
        ytitle("Total Cost (Billions FCFA)")                          ///
        ylabel(, labsize(small))                                      ///
        plotregion(margin(r+15))                                      ///
        scheme(s2color)
    graph export "outputs/graph1a_cost_ranking_absolute.png", replace width(1400)
    display "Graph 1a (Cost Ranking - Absolute) exported."
restore


/*---------------------------------------------------------------------------
   Graphique 1b : Coûts en % du PIB classés
   -------------------------------------------------------------------------
   Même logique que graph1a, avec la part dans le PIB (pct_pib_s?) à la place
   du coût absolu. Couleur maroon pour différencier visuellement les deux graphes.
---------------------------------------------------------------------------*/

preserve
    clear
    set obs 7
    gen cost_pib = .
    gen str50 sc_label = ""

    forvalues s = 1/7 {
        replace cost_pib = pct_pib_s`s' in `s'   // Part dans le PIB (%)
        replace sc_label = "`lab`s''"   in `s'
    }

    gsort -cost_pib

    graph hbar cost_pib,                                              ///
        over(sc_label, sort(cost_pib) descending                      ///
            label(labsize(small) angle(0)))                           ///
        bar(1, color(maroon))                                         ///
        blabel(bar, format(%5.2f) size(small) position(outside)       ///
            color(black))                                 ///
        title("Cost of Cash Transfer Scenarios as % of GDP",          ///
            size(medium))                                             ///
        subtitle("Annual transfer: 200,000 FCFA per eligible household") ///
        ytitle("Cost (% of GDP)")                                     ///
        ylabel(0(0.5)2.5, labsize(small) format(%3.1f))               ///
        plotregion(margin(r+10))                                      ///
        scheme(s2color)
    graph export "outputs/graph1b_cost_ranking_pctgdp.png", replace width(1400)
    display "Graph 1b (Cost Ranking - % GDP) exported."
restore


/*---------------------------------------------------------------------------
   Graphique 2 : FGT0 (Headcount Ratio) avant/après transfert par scénario
   -------------------------------------------------------------------------
   Deux barres par scénario : baseline 2025 (navy) et post-transfert (orange).
   bargap(20) espace les paires de barres pour la lisibilité.
   margin(t+14) réserve l'espace au-dessus pour les étiquettes blabel.
---------------------------------------------------------------------------*/

preserve
    clear
    set obs 7
    gen fgt0_b = .
    gen fgt0_e = .
    gen str50 sc_label = ""

    forvalues s = 1/7 {
        replace fgt0_b   = fgt0_2025*100 in `s'   // Valeur baseline (en %)
        replace fgt0_e   = fgt0_s`s'*100 in `s'   // Valeur post-transfert (en %)
        replace sc_label = "`lab`s''"    in `s'
    }

    graph bar fgt0_b fgt0_e,                                          ///
        over(sc_label, label(labsize(vsmall) angle(45)))               ///
        bar(1, color(navy)) bar(2, color(orange))                      ///
        bargap(20)                                                     ///
        blabel(bar, format(%4.2f) size(vsmall) position(outside)       ///
            color(black))                                 ///
        legend(label(1 "Baseline 2025") label(2 "Post-Transfer")       ///
            size(small))                                               ///
        title("Headcount Ratio (FGT0) Before and After Transfer",      ///
            size(medium))                                              ///
        ytitle("FGT0 (%)")                                             ///
        plotregion(margin(t+14))                                       ///
        scheme(s2color)
    graph export "outputs/graph2_fgt0_before_after.png", replace width(1400)
    display "Graph 2 (FGT0 Before/After) exported."
restore


/*---------------------------------------------------------------------------
   Graphique 3 : FGT1 (Poverty Depth) avant/après transfert par scénario
---------------------------------------------------------------------------*/

preserve
    clear
    set obs 7
    gen fgt1_b = .
    gen fgt1_e = .
    gen str50 sc_label = ""

    forvalues s = 1/7 {
        replace fgt1_b   = fgt1_2025*100 in `s'
        replace fgt1_e   = fgt1_s`s'*100 in `s'
        replace sc_label = "`lab`s''"    in `s'
    }

    graph bar fgt1_b fgt1_e,                                          ///
        over(sc_label, label(labsize(vsmall) angle(45)))               ///
        bar(1, color(navy)) bar(2, color(orange))                      ///
        blabel(bar, format(%4.2f) size(small) position(outside)        ///
            color(black))                                 ///
        legend(label(1 "Baseline 2025") label(2 "Post-Transfer")       ///
            size(small))                                               ///
        title("Poverty Depth (FGT1) Before and After Transfer",        ///
            size(medium))                                              ///
        ytitle("FGT1 (%)")                                             ///
        plotregion(margin(t+12))                                       ///
        scheme(s2color)
    graph export "outputs/graph3_fgt1_before_after.png", replace width(1400)
    display "Graph 3 (FGT1 Before/After) exported."
restore


/*---------------------------------------------------------------------------
   Graphique 4 : FGT2 (Poverty Severity) avant/après transfert par scénario
---------------------------------------------------------------------------*/

preserve
    clear
    set obs 7
    gen fgt2_b = .
    gen fgt2_e = .
    gen str50 sc_label = ""

    forvalues s = 1/7 {
        replace fgt2_b   = fgt2_2025*100 in `s'
        replace fgt2_e   = fgt2_s`s'*100 in `s'
        replace sc_label = "`lab`s''"    in `s'
    }

    graph bar fgt2_b fgt2_e,                                          ///
        over(sc_label, label(labsize(vsmall) angle(45)))               ///
        bar(1, color(navy)) bar(2, color(orange))                      ///
        blabel(bar, format(%4.2f) size(small) position(outside)        ///
            color(black))                                          ///
        legend(label(1 "Baseline 2025") label(2 "Post-Transfer")       ///
            size(small))                                               ///
        title("Poverty Severity (FGT2) Before and After Transfer",     ///
            size(medium))                                              ///
        ytitle("FGT2 (%)")                                             ///
        plotregion(margin(t+12))                                       ///
        scheme(s2color)
    graph export "outputs/graph4_fgt2_before_after.png", replace width(1400)
    display "Graph 4 (FGT2 Before/After) exported."
restore


/*---------------------------------------------------------------------------
   Graphique 5 : Efficacité des scénarios classée par ordre décroissant
   -------------------------------------------------------------------------
   L'efficacité est très petite (ordre de 10⁻¹³ à 10⁻¹⁴).
   Le format %10.2e permet de l'afficher en notation scientifique.
   margin(r+20) ménage l'espace à droite pour les étiquettes.
---------------------------------------------------------------------------*/

preserve
    clear
    set obs 7
    gen eff = .
    gen str50 sc_label = ""

    forvalues s = 1/7 {
        replace eff      = efficacite_s`s' in `s'
        replace sc_label = "`lab`s''"      in `s'
    }

    gsort -eff   // Tri décroissant : le plus efficient en haut

    graph hbar eff,                                                    ///
        over(sc_label, sort(eff) descending                            ///
            label(labsize(small) angle(0)))                            ///
        bar(1, color(teal))                                            ///
        blabel(bar, format(%10.2e) size(small) position(outside)       ///
            color(black))                                          ///
        title("Efficiency of Cash Transfer Scenarios",                 ///
            size(medium))                                              ///
        subtitle("Efficiency = ΔFGT1 / Total Cost")                    ///
        ytitle("Efficiency (ΔFGT1 per FCFA)")                          ///
        plotregion(margin(r+20))                                       ///
        scheme(s2color)
    graph export "outputs/graph5_efficiency_ranking.png", replace width(1400)
    display "Graph 5 (Efficiency Ranking) exported."
restore


/*---------------------------------------------------------------------------
   Graphique 6 : Coefficient de Gini avant/après transfert par scénario
   -------------------------------------------------------------------------
   Format %5.3f pour afficher le Gini à 3 décimales (ex : 0.351).
   L'axe Y est borné entre 0 et 0.45 pour éviter les distorsions visuelles
   liées au fait que les valeurs varient très peu d'un scénario à l'autre.
---------------------------------------------------------------------------*/

preserve
    clear
    set obs 7
    gen gini_b = .
    gen gini_e = .
    gen str50 sc_label = ""

    forvalues s = 1/7 {
        replace gini_b   = gini_2025  in `s'   // Gini baseline 2025
        replace gini_e   = gini_s`s'  in `s'   // Gini post-transfert
        replace sc_label = "`lab`s''" in `s'
    }

    graph bar gini_b gini_e,                                          ///
        over(sc_label, label(labsize(vsmall) angle(45)))               ///
        bar(1, color(navy)) bar(2, color(orange))                      ///
        bargap(20)                                                     ///
        blabel(bar, format(%5.3f) size(vsmall) position(outside)       ///
            color(black))                                  ///
        legend(label(1 "Baseline 2025") label(2 "Post-Transfer")       ///
            size(small))                                               ///
        title("Gini Coefficient Before and After Transfer",            ///
            size(medium))                                              ///
        ytitle("Gini Coefficient")                                     ///
        yscale(range(0 0.45))                                          ///
        plotregion(margin(t+12))                                       ///
        scheme(s2color)
    graph export "outputs/graph6_gini_before_after.png", replace width(1400)
    display "Graph 6 (Gini Before/After) exported."
restore


/*---------------------------------------------------------------------------
   Graphique 7 : Évolution des indices FGT entre 2018 et 2025 (baseline)
   -------------------------------------------------------------------------
   Graphique en barres groupées sur 3 observations (FGT0, FGT1, FGT2).
   Permet de visualiser la tendance entre les deux dates de référence
   sans aucune politique de transfert appliquée.
---------------------------------------------------------------------------*/

preserve
    clear
    set obs 3   // Une observation par indice FGT

    gen str10 fgt_label = ""
    gen val_2018 = .
    gen val_2025 = .

    replace fgt_label = "FGT0 (%)"  in 1
    replace fgt_label = "FGT1 (%)"  in 2
    replace fgt_label = "FGT2 (%)"  in 3

    replace val_2018 = fgt0_2018*100 in 1
    replace val_2018 = fgt1_2018*100 in 2
    replace val_2018 = fgt2_2018*100 in 3

    replace val_2025 = fgt0_2025*100 in 1
    replace val_2025 = fgt1_2025*100 in 2
    replace val_2025 = fgt2_2025*100 in 3

    graph bar val_2018 val_2025,                                       ///
        over(fgt_label, label(labsize(medium)))                        ///
        bar(1, color(navy)) bar(2, color(orange))                      ///
        blabel(bar, format(%5.2f) size(small) position(outside)        ///
            color(black))                                  ///
        legend(label(1 "2018 (Survey)") label(2 "2025 (Aged)")         ///
            size(small))                                               ///
        title("FGT Poverty Indices: 2018 vs 2025 Baseline",            ///
            size(medium))                                              ///
        subtitle("Without any cash transfer policy")                   ///
        ytitle("Index Value (%)")                                      ///
        plotregion(margin(t+12))                                       ///
        scheme(s2color)
    graph export "outputs/graph7_fgt_evolution_2018_2025.png", replace width(1200)
    display "Graph 7 (FGT Evolution 2018-2025) exported."
restore


/*---------------------------------------------------------------------------
   Graphique 8 : Évolution du Gini entre 2018 et 2025 (baseline)
   -------------------------------------------------------------------------
   Barres simples (une par date) montrant la quasi-stabilité du Gini sur
   la période. L'axe Y borné entre 0 et 0.45 évite les effets de distorsion.
---------------------------------------------------------------------------*/

preserve
    clear
    set obs 2   // Une observation par date

    gen str10 year_label = ""
    gen gini_val = .

    replace year_label = "2018"     in 1
    replace year_label = "2025"     in 2
    replace gini_val   = gini_2018  in 1
    replace gini_val   = gini_2025  in 2

    graph bar gini_val,                                                ///
        over(year_label, label(labsize(medium)))                       ///
        bar(1, color(navy))                                            ///
        blabel(bar, format(%5.4f) size(medium) position(outside)       ///
            color(black))                                  ///
        title("Gini Coefficient: 2018 vs 2025 Baseline",               ///
            size(medium))                                              ///
        subtitle("Without any cash transfer policy")                   ///
        ytitle("Gini Coefficient")                                     ///
        yscale(range(0 0.45))                                          ///
        plotregion(margin(t+10))                                       ///
        scheme(s2color)
    graph export "outputs/graph8_gini_evolution_2018_2025.png", replace width(900)
    display "Graph 8 (Gini Evolution 2018-2025) exported."
restore


/*===========================================================================
   RÉCAPITULATIF FINAL
   -------------------------------------------------------------------------
   Tous les fichiers de sortie ont été écrits dans :
     `projet_dir'/outputs/
===========================================================================*/

display " "
display "======================================================="
display "ALL OUTPUTS EXPORTED TO: `projet_dir'/outputs/"
display "======================================================="
display "  EXCEL : results.xlsx"
display "    - Sheet 1 : FGT & Gini Baseline (2018 vs 2025)"
display "    - Sheet 2 : Cost of Scenarios"
display "    - Sheet 3 : FGT Impact by Scenario (National)"
display "    - Sheet 4 : Efficiency Ranking"
display "    - Sheet 5 : FGT Urban-Rural"
display "    - Sheet 6 : Gini by Scenario"
display "  GRAPHS :"
display "    - graph1a_cost_ranking_absolute.png  (Billions FCFA)"
display "    - graph1b_cost_ranking_pctgdp.png    (% of GDP)"
display "    - graph2_fgt0_before_after.png"
display "    - graph3_fgt1_before_after.png"
display "    - graph4_fgt2_before_after.png"
display "    - graph5_efficiency_ranking.png"
display "    - graph6_gini_before_after.png"
display "    - graph7_fgt_evolution_2018_2025.png"
display "    - graph8_gini_evolution_2018_2025.png"
display "======================================================="
