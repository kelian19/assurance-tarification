# Clair — Atelier de tarification

Calculateur métier en français : prime pure a priori, prime bayésienne Poisson-Gamma et crédibilité sur les coûts. Interface responsive avec comparaison des méthodes, frais/marge explicites, export JSON et impression.

## Démarrage

L’interface est autonome, sans dépendance applicative :

```sh
python -m http.server 8000 --directory dist
```

Ouvrir http://localhost:8000. Les calculs du navigateur sont dans `dist/engine.mjs`. Leur référence Python, sans dépendance externe, est dans `python/pricing.py`.

```sh
python -m unittest discover -s tests -v
node tests/test_engine.mjs
python tests/check_parity.py
```

## Parcours métier

1. Choisir un profil illustratif ou saisir la fréquence annuelle et le coût moyen de votre tarif de référence.
2. Saisir des périodes distinctes d’historique : mois assurés, nombre de sinistres et charge totale.
3. Choisir le tarif initial, la prime bayésienne ou la crédibilité sur les coûts.
4. Ajouter éventuellement frais et marge, puis calculer, comparer, exporter ou imprimer.

La prime annuelle est distinguée de la prime de la durée du contrat. Le montant proposé est hors taxes et frais de fractionnement. La mensualisation affichée est un simple quotient.

## Hypothèses

- Les profils et paramètres initiaux sont **illustratifs et non calibrés**. Aucun GLM n’a encore été entraîné. Le tarif peut être remplacé par les hypothèses de l’utilisateur.
- Gamma est en convention forme/taux : alpha = fréquence × beta ; fréquence a posteriori = (alpha + nombre de sinistres) / (beta + exposition).
- La méthode bayésienne ajuste la fréquence et conserve le coût moyen initial. Elle calcule une espérance et aucun chargement d’incertitude.
- La crédibilité utilise Z = exposition / (K + exposition). K doit être estimé sur un portefeuille homogène. Pour les années pleines, il s’agit de la formule de Bühlmann du cours ; les durées partielles utilisent l’extension pondérée de type Bühlmann-Straub, avec variance inversement proportionnelle à l’exposition.
- Historique et tarif initial doivent correspondre à un risque comparable. Éviter de compter deux fois un historique déjà intégré au bonus-malus.
- Montant HT = (prime pure de la période + frais fixes) / (1 − frais variables − marge), les deux taux étant exprimés en proportion du montant HT.
- Aucune donnée saisie n’est stockée automatiquement ni envoyée à un serveur par l’application. Le navigateur charge les polices depuis Google Fonts.

## Suite du projet

Entraîner et valider des GLM fréquence/sévérité sur freMTPL2 ; estimer la surdispersion et les paramètres de crédibilité ; brancher les modèles validés au calculateur. Préserver la distinction entre historique réel et démonstration.

[Plan et audit des scripts](docs/PLAN.md)
