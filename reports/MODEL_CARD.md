# Calibration actuarielle — fremtpl2-2026-11-v1

## Décision de validation
**Simulation uniquement ; validation commerciale non acquise.** Le modèle est réellement entraîné sur freMTPL2, mais son niveau de charge sur le test et les données manquantes pour une validation compagnie empêchent de le qualifier de tarif de production.

La charge de test observée vaut 10,331,030.93 EUR contre 12,535,407.63 EUR prédits. O/P = 0.8241, soit une prédiction supérieure de 21.34 % à la charge observée. Intervalle d’échantillonnage bootstrap du ratio : [0.7261, 0.9279] (300 réplications Poisson au niveau contrat). Cet intervalle ne représente ni une distribution prédictive de sinistres ni toute l’incertitude du modèle.

Aucun recalage sur le test n’est appliqué. Les seuils de contrôle proposés sont documentés dans acceptance.json ; ils ne sont pas revendiqués comme préenregistrés. Le test est désormais connu : tout nouveau réglage nécessite une nouvelle validation externe pour une approbation indépendante.

## Données et audit
Source originale CASdatasets, commit 227fb56b8734bdb7c0327a41180e01d2ddaeaf26. 677,991 contrats uniques et 26,444 montants de sinistres. Aucun sinistre orphelin, aucune incohérence nombre/montants. Les tables ont été agrégées avant jointure ; l’exposition n’est pas dupliquée.

Les 1 224 expositions supérieures à un an sont conservées comme durées observées. Les 8 contrats avec plus de 4 sinistres sont conservés : aucune troncature arbitraire du nombre. Les gros sinistres sont conservés dans les objectifs d’évaluation ; la sévérité plafonnée à 100 000 EUR, avec recharge explicite des excédents, a été comparée comme modèle concurrent.

La source ne fournit pas de calendrier exploitable ou de liens longitudinaux fiables entre assurés. La séparation se fait par identifiant de contrat, sans garantie de regroupement par conducteur réel. La période est approximativement 2011–2013 selon la documentation. Aucune inflation, évolution de garanties ou actualisation du portefeuille n’est déduite de données absentes.

## Protocole d'estimation
Découpage stable SHA256 par contrat : train 407,317, validation 135,471, test 135,203. Les sinistres suivent le découpage de leur contrat. Les bornes d’âge, de puissance et d’ancienneté sont définies explicitement, sans utiliser la cible. L’encodeur est ajusté sur train uniquement.

Variables : âge du conducteur et du véhicule par tranches, puissance fiscale par tranches, carburant, zone et région historique. Exclusion de BonusMalus pour éviter de réutiliser explicitement le même historique dans la mise à jour a posteriori. Les effets sont des associations tarifaires, pas des effets causaux.

- Fréquence : GLM Poisson, lien log ; nombre/exposition avec pondération par exposition, équivalent à un offset log(exposition). Trois pénalisations comparées sur validation. Alpha retenu : 0.0.
- Sévérité : GLM Gamma à lien log, sinistres positifs au niveau sinistre. Trois pénalisations, avec et sans plafond/recharge. Choix sur la déviance Tweedie de prime pure sur validation. Alpha retenu : 0.001, plafond retenu : None. Recalage multiplicatif de niveau estimé sur train uniquement : 1.045189.
- Les modèles restent ajustés sur train ; aucun réajustement sur validation ou test.

## Résultats hors échantillon
| Indicateur | Validation | Test |
|---|---:|---:|
| O/P nombre | 0.9968 | 0.9892 |
| O/P charge | 0.9463 | 0.8241 |
| Déviance Poisson | 0.471479 | 0.468711 |
| Déviance Tweedie p=1,5 | 83.856452 | 80.511264 |
| Déviance Tweedie du tarif uniforme | 87.053129 | 80.845144 |

Le gain de déviance de prime pure sur test est de 0.41 %. Ce faible gain de classement/ajustement ne compense pas le défaut de niveau agrégé. Les résultats par segment, y compris les mauvais résultats, sont dans test_segments.csv.

## Diagnostics de dispersion
Sur train, la dispersion de Pearson du Poisson vaut 1.7644. Le ratio résiduel rapporté à la variance NB2 vaut 1.7083, donc le mélange NB2 ne résout pas toute la surdispersion.

La forme Gamma estimée par vraisemblance, moyennes figées, vaut 0.7603 (dispersion 1.3154). Le second moment relatif empirique vaut 30.0965, très éloigné du moment impliqué par cette Gamma. Les 10 plus gros sinistres représentent 21.41 % de la charge d’apprentissage : l’hypothèse de queue Gamma mérite une revue.

## Personnalisation bayésienne
On pose U ~ Gamma(r,r), de moyenne 1, et N | U ~ Poisson(e × lambda(x) × U). La vraisemblance marginale binomiale négative est maximisée sur train, avec les moyennes du GLM figées : r = 0.698413.

Pour un profil inchangé : beta(x) = r/lambda(x), alpha = r. Après n sinistres et t années, fréquence ajustée = (r+n)/(r/lambda+t). Pour des profils historiques différents, il faudrait sommer leurs fréquences attendues pondérées par exposition ; cette V1 impose un risque comparable.

Ce r remplace le réglage illustratif beta=4. Son interprétation comme hétérogénéité persistante est une hypothèse : le panel annuel ne distingue pas une hétérogénéité durable d’une surdispersion transitoire. La performance de renouvellement n’est donc pas validée longitudinalement.

## Crédibilité sur les coûts
Faute de panel, les paramètres de Bühlmann ne sont pas estimés non paramétriquement. Une crédibilité **structurelle** est dérivée du même modèle collectif :

v(x) = lambda(x) × E[Y²|x] ; a(x) = lambda(x)² × m(x)² / r.

K(x) = r/lambda(x) × q, avec q = E[(Y/m(x))²] estimé sur train = 30.096451.

On suppose le second moment relatif constant entre profils. Z = t/(K+t). Cette hypothèse, très sensible aux gros sinistres, est explicite ; elle ne constitue pas une validation de la crédibilité non paramétrique du cours. Pour des périodes fractionnaires, l’hypothèse de variance inversement proportionnelle à l’exposition est requise.

## Base économique et chargements
Les résultats sont en euros historiques de la source. L’interface permet un facteur d’évolution des coûts fourni par le métier, conservé dans l’export. Un facteur égal à 1 n’actualise pas le tarif. Les charges historiques saisies doivent déjà être exprimées dans la même base monétaire que le coût moyen ajusté.

Montant HT = (exposition future × prime pure annuelle + frais fixes) / (1 − taux de frais − taux de marge). Les taux restent des hypothèses métier, initialisées à zéro : ils ne peuvent pas être calibrés sur une base de seuls contrats/sinistres. Aucune fiscalité ou charge de réassurance n’est inventée.

## Travaux requis avant lancement compagnie
1. Obtenir le portefeuille récent, les garanties, limites/franchises, bases monétaires et périmètre de réassurance ; travailler sur des coûts développés à l’ultime.
2. Diagnostiquer la sévérité : répartition des gros sinistres, validation temporelle, modélisation séparée de la queue et stabilité des segments. Le test courant reste un diagnostic déjà consulté.
3. Valider sur un panel de renouvellement la persistance du risque individuel ; estimer la crédibilité non paramétrique si les données le permettent.
4. Renseigner frais, taxes, marge et objectif de rentabilité/capital ; faire approuver les seuils et le tarif par la fonction actuarielle et le métier.
5. Mettre en place validation indépendante, journalisation serveur et droits d’accès si l’outil sert effectivement à émettre des offres. L’application actuelle calcule dans le navigateur et exporte un dossier ; elle n’est pas un système de souscription.

## Suivi proposé
Contrôler exposition, mix de risques, modalités inconnues, fréquence, sévérité, ratio O/P global et par segment, gros sinistres et dérive des entrées. Revue mensuelle des indicateurs avec une fenêtre suffisamment mature et revue formelle après tout changement de modèle. Aucun recalibrage automatique à partir des simulations saisies.
