# Clair — Tarification automobile calibrée

Interface métier en français, moteur Python, GLM fréquence/sévérité réellement entraînés sur **freMTPL2** et personnalisation bayésienne / crédibilité structurelle.

**Statut : calibration historique réalisée ; simulation uniquement.** Le test révèle une surestimation de la charge. Le tarif ne dispose pas d’une validation commerciale ou temporelle sur un portefeuille récent.

## Résultats constatés

- 677 991 contrats et 26 444 sinistres, source originale CASdatasets figée au commit `227fb56b8734bdb7c0327a41180e01d2ddaeaf26`.
- Apprentissage : 407 317 contrats ; validation : 135 471 ; test : 135 203. Découpage stable par police avant préparation et réglage.
- Sur test : ratio observé/prédit des nombres **0,989** ; ratio des charges **0,824**.
- Charge test observée : **10,33 M€**, prédite : **12,54 M€**. Le défaut de calibration agrégée est publié, sans recalage sur le test.
- Paramètre de mélange Poisson-Gamma `r = 0,6984` estimé sur apprentissage ; `beta(x) = r / fréquence(x)`.
- Crédibilité sur les coûts : `K(x) = beta(x) × q`, second moment relatif empirique `q = 30,0965`. Cette estimation est structurelle, sensible aux gros sinistres et non validée longitudinalement.

[Rapport et limites](reports/MODEL_CARD.md) · [Contrôles d’acceptation](reports/acceptance.json) · [Résultats complets](reports/calibration.json) · [Segments de test](reports/test_segments.csv)

## Utiliser l’interface

```sh
python -m http.server 8000 --directory dist
```

Ouvrir http://localhost:8000. Renseigner le conducteur, le véhicule et la zone ; la fréquence, le coût moyen, beta et K sont calculés par le modèle versionné. Saisir un historique réel sur un profil comparable, puis choisir tarif initial, prime bayésienne ou crédibilité structurelle. Sans historique, la prime ajustée rejoint le tarif initial.

Les résultats sont en euros historiques de la source, approximativement 2011–2013. Le facteur d’évolution des coûts doit être justifié par le métier. Les charges historiques doivent être dans la même base monétaire. Frais et marge sont des hypothèses métier explicites, initialisées à zéro ; taxes et fractionnement sont exclus. Un montant simulé n’est pas un devis engageant.

L’onglet **Calibration & validation** expose le protocole, les indicateurs de train/validation/test et les réserves de validation. Export JSON : profil, historique, modèle, empreinte, base économique, hypothèses et résultats. Impression de synthèse disponible. Aucun historique n’est enregistré automatiquement ni envoyé à un serveur par l’application.

## Reproduire la calibration

Python 3.12, dépendances versionnées dans requirements.txt. Les données brutes restent hors Git ; leurs URLs et empreintes sont dans reports/data_manifest.json.

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python pipeline/calibrate.py
.venv/bin/python pipeline/diagnostics.py
.venv/bin/python pipeline/report.py
```

La source est figée et vérifiée par empreintes. Le modèle est ajusté sur train ; les pénalisations et la variante de sévérité sont choisies sur validation. Le test est réservé à l’évaluation. Le pipeline ne recale aucun paramètre sur ce test. Ce test ayant désormais été consulté, une future modification requiert un nouveau jeu indépendant pour une approbation de production.

## Tests

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tests/check_parity.py
node tests/test_engine.mjs
node tests/test_calibrated_parity.mjs
```

Le moteur navigateur est autonome. `python/model.py` et `dist/model.mjs` appliquent les mêmes coefficients exportés, avec contrôles de domaine. Les tests de parité couvrent 36 situations de calcul et 24 profils synthétiques, sans publier de données individuelles de la base.

## Architecture et hypothèses

- `pipeline/` : téléchargement, audit, calibration, diagnostics et documentation.
- `artifacts/model.json` : coefficients, paramètres, domaines et version du modèle.
- `python/` : moteur de prime et prédiction du GLM exporté.
- `dist/` : interface autonome et artefacts de consultation.
- `reports/` : protocole, métriques, sensibilité aux grands sinistres, sources et décision de validation.
- `tests/` : invariants actuariels, domaines et parité Python/navigateur.

Poisson à lien log avec exposition ; Gamma à lien log pour les coûts. Le bonus-malus est exclu du tarif initial afin d’éviter une réutilisation explicite du même historique. La mise à jour Poisson-Gamma suppose une hétérogénéité persistante : cela reste à valider sur un panel de renouvellements. La crédibilité non paramétrique de Bühlmann n’est pas estimable à partir de cette seule coupe annuelle ; une crédibilité structurelle documentée est utilisée à sa place.

La source ne permet pas de vérifier les garanties actuelles, la maturité à l’ultime, les taxes, les frais compagnie, la réassurance ou l’inflation propre à la branche. Une mise en production exige ces éléments, une revue actuarielle indépendante et un suivi des dérives. L’application actuelle n’est pas un système d’émission d’offres.

[Plan et audit initial](docs/PLAN.md)

## Note méthodologique à partager

[PDF — méthodes et mathématiques](docs/latex/note_tarification.pdf) · [Source LaTeX](docs/latex/note_tarification.tex).
La note comporte quatre figures (calibration agrégée, ratios observé/prédit par segment, Poisson contre NB2 et gros sinistres, personnalisation), générées par `python -m pipeline.make_figures` (dépendance : `matplotlib`) à partir des rapports versionnés ; l'exemple chiffré de la note y est recalculé et contrôlé.
