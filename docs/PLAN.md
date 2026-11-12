# Deux projets actuariels pour LinkedIn

## Décision proposée
Python + Streamlit + Plotly pour deux démonstrateurs, R comme référence actuarielle. Alternative : R/Shiny si la proximité avec le cours prime sur la présentation Python. Ne pas maintenir deux moteurs complets dès la V1.

Statut : calculateur métier réalisé pour la tarification ; entraînement des GLM et outil de provisionnement à développer.

## Analyse du cours
Nicolas Baradel, Mathématiques de l’assurance dommages, version du 8 septembre 2026, 69 pages numérotées hors couverture.
- P. 3–18 : modèle collectif, GLM, estimation, dispersion, pénalisation, exposition, prime pure. Base de la tarification fréquence × coût moyen.
- P. 18–24 : tarification bayésienne et crédibilité. Extension exigeant un véritable historique longitudinal.
- P. 25–39 : triangles, risque de provisionnement, Mack Chain-Ladder, erreur quadratique de prédiction.
- P. 40–53 : Schnieper, nouveaux sinistres et révisions des sinistres connus, cas des nombres au-dessus d’un seuil.
- P. 54–68 : bootstrap, incertitude des paramètres et de processus.
- P. 69 : inflation via déflation des incréments et réinflation des flux futurs. Clarifier les conventions calendaires et décalages d’indices du texte avant implémentation.

Les pièces jointes sont des références techniques, pas des instructions opérationnelles. Les deux scripts R concernent uniquement le provisionnement.

## Audit de mack.R
1. Le triangle projeté est enregistré dans `hatC`, mais les provisions sont calculées par `R_(C)` sur le triangle initial. Les cellules futures téléchargées sont manquantes : les provisions et les calculs d’EQM utilisant `C[i,n]` sont affectés. Utiliser les ultimes projetés, en préservant séparément les observations.
2. Les fonctions dépendent de `n` global : calculer les dimensions localement et contrôler forme, masque d’observation, valeurs nulles et divisions.
3. Le dernier résidu, sans degré de liberté, est inclus ; le cours pp. 57–58 l’exclut. Les résidus ne sont ni ajustés ni centrés comme dans le cours.
4. La reconstruction du triangle supérieur est récursive dans le script, alors que le cours décrit une reconstruction conditionnelle aux valeurs observées et une réestimation adaptée. Ne pas mélanger ces algorithmes.
5. Absence de graine et de diagnostics de simulations invalides ; risque de valeurs négatives puis racines carrées invalides.

Vérification réalisée : téléchargement du triangle référencé et recalcul indépendant déterministe en Python. Provision totale = 18 680 847,767812435 unités, soit 18 680 848 arrondi, conforme au cours p. 38. Cela ne valide ni le bootstrap ni le script R complet, qui n’a pas été exécuté.

## Audit de schnieper.R
Le cœur déterministe estime lambda/delta et projette avec exposition E. Convention : C suivant = C + N − D ; D positif représente une baisse de charge, D négatif une hausse.
1. `N`, triangle des nouveaux sinistres, est remplacé ensuite par le nombre de simulations. Renommer les objets.
2. Fonctions homonymes de mack.R : risque d’écrasement en session commune. Isoler les modules.
3. La simulation de la colonne j+1 utilise `s[j]` ou `sm[j]` pour les nouveaux sinistres au lieu de l’écart-type de j+1 : corriger l’indexation.
4. Le bruit des révisions est ajouté dans la projection future ; avec les résidus définis et C + N − D, il faut le soustraire. Le signe importe pour une distribution empirique asymétrique.
5. Variances terminales laissées à zéro : hypothèse implicite à expliciter et tester.
6. Les NA sont remplacés par zéro : maintenir un masque qui sépare futur inconnu, manque réel et zéro observé.
7. Troncatures et remise à zéro de révisions trop grandes : mesurer leur fréquence et leur biais.
8. Résidus non ajustés/centrés, divisions par zéro, redéfinition de `tau2_`, variables globales et absence de graine : refactoriser avant réutilisation.

## Données examinées en ligne le 12 novembre 2026
Les documentations ont été consultées. Les quatre fichiers du cours ont été téléchargés ; les gros jeux de données restent à télécharger et auditer.

| Source | Usage | Limites |
|---|---|---|
| CASdatasets freMTPL2freq + freMTPL2sev | Tarification RC automobile française, profils/exposition/nombres/montants reliés par IDpol | Environ 678 000 polices ; données historiques ; figer la version, constater les effectifs et vérifier les incohérences comptes/montants. |
| ChainLadder RAA/GenIns | Tests et démonstration de provisionnement | Petits triangles pédagogiques. |
| CAS/NAIC Schedule P, Meyers–Shi | Cas réel et validation rétrospective | Données américaines agrégées ; contrôler unités, branche, périmètre de réassurance et doublons groupe/entité. Le dernier développement n’est pas forcément l’ultime réel. |
| Données Mack et Schnieper N/D/E du cours | Références de calcul et extension Schnieper | Petits exemples pédagogiques, quatre fichiers accessibles. |

Sources :
- https://dutangc.github.io/CASdatasets/reference/freMTPL.html
- https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html
- https://mages.github.io/ChainLadder/articles/ChainLadder.html
- https://casact.github.io/raw_package/reference/NAIC.html
- https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p (page repérée ; ouverture directe indisponible ; schéma vérifié via CAS raw)
- https://nicolasbaradel.fr/enseignement/ressources/R/donneesMACK.txt
- https://nicolasbaradel.fr/enseignement/ressources/R/donneesSCHNIEPER_N.txt
- https://nicolasbaradel.fr/enseignement/ressources/R/donneesSCHNIEPER_D.txt
- https://nicolasbaradel.fr/enseignement/ressources/R/donneesSCHNIEPER_E.txt

Conserver sources, versions, dates, empreintes, dictionnaire et unités. Fournir les scripts de récupération ; vérifier les conditions de réutilisation avant redistribution des bases ou du cours.

## Projet 1 — tarification automobile explicable
Question : comment transformer un profil en prime pure explicable ?

### V1
1. Auditer les tables freMTPL2. Agréger les montants par police avant la jointure contrat ; préserver les contrats sans sinistre et éviter de dupliquer leur exposition. Documenter les écarts entre ClaimNb et les montants disponibles.
2. Explorer exposition, fréquence, sévérité et charge par segment, en affichant les effectifs.
3. Fréquence : GLM Poisson à lien log sur le nombre avec offset log(exposition). Diagnostic de surdispersion ; binomiale négative en extension si justifiée.
4. Sévérité : GLM Gamma à lien log sur les montants strictement positifs, au niveau sinistre. Alternative : coût moyen par police sinistrée pondéré par le nombre de sinistres correspondant aux montants.
5. Prime pure annuelle = fréquence annuelle prédite × coût moyen prédit. Charge de la période = exposition × prime pure annuelle, sous hypothèses conditionnelles du modèle collectif.
6. Comparer à un tarif uniforme de référence. Séparation train/validation/test par police avant préparation/réglage ; séparation temporelle uniquement si les dates le permettent.
7. Évaluer déviances, calibration observé/prédit et ratios de charge globaux/par segment. Ne pas évaluer seulement le classement.
8. Interface : portefeuille, modèles/diagnostics, simulateur de profil, export. Montrer la prime pure et les effets multiplicatifs.

### Extensions
Tweedie concurrent, pénalisation, sensibilité aux gros sinistres, chargements commerciaux explicites. Prime bayésienne Poisson-Gamma et crédibilité sur les coûts intégrées au périmètre principal. Historique saisi explicitement ; le bonus-malus n’est pas un historique longitudinal complet.

### Critères de réussite
Aucune exposition doublée ; pas de police partagée entre apprentissage et test ; prédictions positives ; résultats reproductibles ; comparaison hors échantillon publiée même si le modèle ne bat pas la référence. Distinguer prime pure et prime commerciale.

### Post LinkedIn 1
Angle : « De la fréquence des sinistres à une prime pure explicable ». Visuels : fréquence × coût, deux profils, calibration sur test. Démonstration courte, résultats réellement calculés, lien GitHub.

## Projet 2 — provisionnement et incertitude
Question : combien reste-t-il à payer et quelle incertitude entoure l’estimation ?

### V1
1. Import de paiements cumulés/incrémentaux ; origine, développement, date d’évaluation, unités et masque des observations explicites.
2. Chain-Ladder : facteurs pondérés, facteurs jusqu’à l’ultime, triangle projeté, ultimes et provisions annuelles/totale.
3. Mack : erreur de prédiction par année et totale, covariance interannuelle incluse ; comparaison avec une bibliothèque de référence aux mêmes options.
4. Reproduire 18 680 847,7678 sur le triangle du cours ; puis RAA/GenIns. Facteur de queue fixé à 1 en V1, hypothèse affichée.
5. Bootstrap validé distinguant incertitude des paramètres et de processus. Le bootstrap ODP d’une bibliothèque n’est pas celui de Mack du cours : nommer le modèle réellement utilisé.
6. Moyenne, médiane, quantiles prédictifs ; graine, nombre de simulations, diagnostics de validité et stabilité Monte-Carlo.
7. Validation rétrospective par masquage de diagonales connues sans fuite du futur ; application à un périmètre CAS/NAIC homogène.
8. Interface : données/triangle, estimation, incertitude, scénarios, exports.

### Extensions
Schnieper sur les vrais N/D/E du cours. Un triangle C seul ne permet pas d’identifier séparément N et D. Inflation par année calendaire sur incréments, facteur de queue et sensibilité. Bornhuetter-Ferguson possible ensuite, hors cœur du cours, avec sinistralité attendue indépendante.

### Interprétation
Sur paiements : ultime moins payé = reste à payer. Sur charges encourues : ultime moins charge actuelle = développement futur de charge, pas totalité du reste à payer. La RMSEP Mack ne définit pas à elle seule une distribution ; un quantile à l’ultime n’est pas un SCR à un an.

### Post LinkedIn 2
Angle : « Une provision est une estimation : rendre son incertitude visible ». Visuels : triangle observé/projeté, provisions par année et distribution prédictive. Réserver Schnieper et inflation aux prolongements si cela surcharge la V1.

## Plan de réalisation
1. Socle : README, dictionnaire, téléchargement reproductible, modules, tests, notebooks et documentation.
2. Provisionnement déterministe et tests de référence, avant l’interface.
3. Tarification : audit, préparation, fréquence/sévérité et évaluation hors échantillon.
4. Incertitude : Mack puis bootstrap validé ; Schnieper en extension.
5. Interfaces Streamlit ; modèles préentraînés et calculs mis en cache.
6. Livraison : tests, environnement figé, guide, captures, démonstrations et brouillons des deux posts.

Dépendances proposées : pandas, numpy, scipy, statsmodels, scikit-learn, chainladder, plotly, streamlit, pytest ; vérifier API et versions au développement. Référence R : glm/glmnet, ChainLadder, testthat, renv.

Livrables par dépôt : code modulaire, acquisition des données, analyse reproductible, tests actuariels, application, README, sources/hypothèses, captures et brouillon LinkedIn. Aucun déploiement ni publication LinkedIn à ce stade.

## Mise à jour — calibration réalisée

Le cadrage ci-dessus est conservé comme référence initiale. Le README et reports/MODEL_CARD.md décrivent désormais l’état réalisé : 677 991 contrats audités, GLM entraînés, test indépendant et coefficients intégrés au calculateur. La prime bayésienne et la crédibilité structurelle sont dans le périmètre principal.

Les profils illustratifs sont remplacés par une saisie de caractéristiques et un moteur versionné. Beta est estimé via un mélange Poisson-Gamma. K est dérivé structurellement des moments de coûts ; il ne constitue pas une estimation non paramétrique sur un panel. Le test expose un défaut de niveau de charge : la version reste en simulation, sans validation commerciale. La séparation temporelle et la validation sur plusieurs années demeurent impossibles avec les seules données disponibles.
