# Note méthodologique — tarification

- `note_tarification.tex` : source LaTeX autonome.
- `note_tarification.pdf` : version compilée, six pages A4.

Compilation (deux passes pour la pagination) :

```sh
pdflatex -interaction=nonstopmode -halt-on-error note_tarification.tex
pdflatex -interaction=nonstopmode -halt-on-error note_tarification.tex
```

Dépendances TeX : classes usuelles, Latin Modern, babel avec locale française importable, amsmath, booktabs, tabularx, microtype, xcolor, tcolorbox, enumitem, fancyhdr, lastpage, titlesec et hyperref. Aucun fichier d'image externe n'est nécessaire.

Les formules décrivent les méthodes réellement utilisées. Les exemples d'historique hypothétique sont identifiés comme tels ; les résultats mesurés et les extensions prévues sont distingués. Documents préparés pour accompagner une présentation du projet ; aucune publication LinkedIn effectuée.
