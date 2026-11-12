# Poisson ou binomiale négative : comparaison mesurée

## Protocole
Le challenger NB2 est ajusté sur les mêmes 407 317 contrats d’apprentissage, avec les mêmes caractéristiques et l’offset log(exposition). Ses coefficients et son paramètre r sont estimés conjointement par maximum de vraisemblance. Le modèle de coût est conservé : cette expérience isole le choix de loi de fréquence.

Le test v1 a déjà été consulté. Cette nouvelle comparaison constitue un diagnostic, pas une nouvelle validation indépendante. Aucun changement n’est appliqué au calculateur publié.

## Modèles
Poisson : N_i ~ Poisson(mu_i), mu_i = exposition_i × exp(x_i' beta), Var(N_i | x_i) = mu_i.

NB2 : N_i ~ NB2(mu_i,r), avec la même forme de moyenne et Var(N_i | x_i) = mu_i + mu_i²/r.

Le mélange U_i ~ Gamma(r,r), N_i | U_i ~ Poisson(exposition_i × lambda_i × U_i) redonne la NB2 marginale. C’est aussi le socle de la personnalisation bayésienne. La surdispersion ne suffit cependant pas à démontrer que l’hétérogénéité est persistante d’une année à l’autre.

## Résultats
| Indicateur | Poisson | NB2 |
|---|---:|---:|
| Log-vraisemblance négative moyenne, validation | 0,162524 | 0,161743 |
| Déviance Poisson de fréquence, validation | 0,471479 | 0,471505 |
| O/P nombre, test déjà consulté | 0,9892 | 0,9807 |
| O/P charge, test déjà consulté | 0,8241 | 0,8156 |
| Charge prédite, test | 12,535 M€ | 12,666 M€ |
| Déviance Tweedie de prime pure, test | 80,5113 | 80,5436 |

r NB2 ajusté conjointement = 0,6950 ; convergence en 66 itérations. Le gradient analytique a été vérifié par différences finies sur un exemple synthétique. Les valeurs complètes sont dans poisson_vs_nb.json.

La NB2 décrit mieux la distribution des nombres au sens de la vraisemblance, mais dégrade légèrement ici les critères de moyenne et de prime pure. Le Poisson reste le modèle de référence du calculateur. Cette conclusion est propre à ces caractéristiques et à ce protocole ; elle ne démontre pas une supériorité générale du Poisson.

## Diagnostic de sévérité et corrections à étudier
Sur le test Poisson, le ratio de charge O/P 0,8241 se décompose en ratio de nombre O/P 0,9892 et rapport de coûts moyens agrégés 0,8331. Ce dernier compare le coût observé par sinistre au coût moyen prédit pondéré par les nombres prédits ; il s’agit d’une décomposition descriptive, pas d’une preuve causale.

Les 10 plus gros sinistres représentent 21,41 % de la charge d’apprentissage, le plus gros 10,82 %. Le coût moyen par sinistre vaut environ 2 367 € en apprentissage, 2 248 € en validation et 1 974 € en test. Cela justifie une analyse de stabilité de la sévérité et de la queue.

Le plafond à 100 000 € avec recharge explicite des excédents a déjà été comparé dans la V1 ; sa déviance de validation ne justifiait pas sa sélection. Un plafonnement seul ne corrige pas le coût total : il change la cible et sous-estime les gros sinistres.

Travaux à mener sur apprentissage/validation uniquement :
1. Validation croisée interne de la stabilité des moyens et des effets des gros sinistres ; publication de résultats par tranche de coûts.
2. Comparaison Gamma, modèle à deux composantes et modèle Tweedie direct. Pour un seuil u, utiliser E[Y|x] = E[min(Y,u)|x] + P(Y>u|x) × E[Y-u|Y>u,x] ; conserver toutes les charges pour l’évaluation totale. Avec seulement 24 sinistres d’apprentissage au-dessus de 100 000 €, la queue ne peut pas supporter une segmentation fine.
3. Étude d’un recalage global seulement sur une période ou un échantillon de calibration approprié ; aucun facteur 0,824 calculé sur le test ne doit être appliqué pour prétendre obtenir une nouvelle validation.
4. Nouvelle évaluation externe sur données récentes, garanties et maturité comparables. Le test v1 reste un diagnostic déjà connu.

## Présentation LinkedIn
Le projet est présentable comme démonstrateur actuariel reproductible avec une validation documentée et des limites explicites. Présenter les résultats négatifs et la comparaison Poisson/NB2 ; éviter les affirmations de performance commerciale, de tarif actuel ou de personnalisation validée sur plusieurs années.

Sources :
- https://www.statsmodels.org/stable/generated/statsmodels.discrete.discrete_model.NegativeBinomial.html
- https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html
