# Note méthodologique — tarification

- `note_tarification.tex` : source LaTeX.
- `note_tarification.pdf` : version compilée, sept pages A4, avec quatre figures.
- `figures/*.pdf` : figures vectorielles, générées par `python -m pipeline.make_figures` depuis `reports/*.json`, `reports/test_segments.csv`, `artifacts/model.json` et le moteur de prime. Les montants de l'exemple chiffré (157,84 € ; 117,27 € ; 156,05 €) sont recalculés et contrôlés à chaque génération. Aucune donnée individuelle n'est requise.

Compilation (deux passes pour la pagination ; le préambule choisit seul les polices selon le moteur) :

```sh
pdflatex -interaction=nonstopmode -halt-on-error note_tarification.tex
pdflatex -interaction=nonstopmode -halt-on-error note_tarification.tex
```

Le PDF publié a été compilé avec [Tectonic](https://tectonic-typesetting.github.io) (moteur XeTeX) : `tectonic -X compile note_tarification.tex`. Les deux moteurs sont acceptés.

Dépendances TeX : classes usuelles, Latin Modern, iftex (fontspec sous XeTeX), babel avec locale française importable, amsmath, graphicx, caption, booktabs, tabularx, microtype, xcolor, tcolorbox, enumitem, fancyhdr, lastpage, titlesec et hyperref. Dépendances Python des figures : `matplotlib`, en plus de `requirements.txt`.

Les formules décrivent les méthodes réellement utilisées. Les exemples d'historique hypothétique sont identifiés comme tels ; les résultats mesurés et les extensions prévues sont distingués. Documents préparés pour accompagner une présentation du projet ; aucune publication LinkedIn effectuée.
