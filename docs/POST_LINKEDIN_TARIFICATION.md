# Brouillon — à relire avant publication

J’ai construit un calculateur de tarification automobile qui va du profil assuré à une prime expliquée : GLM de fréquence, GLM de coût, puis personnalisation bayésienne et crédibilité sur les coûts.

La calibration utilise 677 991 contrats freMTPL2 et 26 444 sinistres, avec trois échantillons séparés par police : apprentissage, validation et test.

Le résultat le plus instructif vient du test : la fréquence est proche de l’observé (ratio observé/prédit de 98,9 %), mais le niveau de charge ne l’est pas : 10,33 M€ observés pour 12,54 M€ prédits.

J’ai conservé ce résultat et la réserve de validation dans l’outil. Une amélioration de déviance ne suffit pas à rendre un tarif prêt pour une compagnie.

Le chantier suivant porte sur les grands sinistres, les données récentes et l’historique longitudinal nécessaire pour valider la personnalisation.

Code, hypothèses, métriques et limites : https://github.com/kelian19/assurance-tarification

#Actuariat #Assurance #Python #Tarification
