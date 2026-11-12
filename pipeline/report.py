"""Documentation, critères d'acceptation et jeu de parité, sans modification du modèle."""
import hashlib,json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from python.model import predict

def main():
 report=json.loads((ROOT/'reports/calibration.json').read_text());model=json.loads((ROOT/'artifacts/model.json').read_text())
 train,val,test=report['metrics'];ratio=test['observed_predicted_cost']
 decision={'status':'simulation_only','model_version':model['version'],'artifact_sha256':hashlib.sha256((ROOT/'artifacts/model.json').read_bytes()).hexdigest(),
 'checks':[{'name':'Exactitude contrats / montants','pass':report['data_audit']['count_amount_mismatches']==0},
 {'name':'Comptage test O/P entre 0,95 et 1,05','pass':.95<=test['observed_predicted_count']<=1.05},
 {'name':'Charge test O/P entre 0,90 et 1,10','pass':.9<=ratio<=1.1},
 {'name':'Déviance prime pure inférieure au tarif uniforme sur test','pass':test['pure_tweedie_deviance_p15']<test['pure_baseline_deviance_p15']},
 {'name':'Validation temporelle sur données récentes compagnie','pass':False},
 {'name':'Validation de personnalisation sur historique longitudinal','pass':False},
 {'name':'Validation frais / taxes / garanties / réassurance par la compagnie','pass':False}],
 'threshold_origin':'Seuils proposés de revue métier, définis comme contrôles de publication ; ils ne sont pas présentés comme préenregistrés avant observation du test.',
 'test_reuse_policy':'Ne pas ajuster sur ce test. Toute nouvelle itération le traite comme référence de diagnostic déjà consultée et requiert un nouveau jeu externe pour approbation.'}
 (ROOT/'reports/acceptance.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2))
 shutil.copy(ROOT/'reports/calibration.json',ROOT/'dist/calibration.json');shutil.copy(ROOT/'reports/acceptance.json',ROOT/'dist/acceptance.json')
 ci=report['test_aggregate_cost_op_bootstrap95'];gain=(1-test['pure_tweedie_deviance_p15']/test['pure_baseline_deviance_p15'])*100
 text=f'''# Calibration actuarielle — {model['version']}

## Décision de validation
**Simulation uniquement ; validation commerciale non acquise.** Le modèle est réellement entraîné sur freMTPL2, mais son niveau de charge sur le test et les données manquantes pour une validation compagnie empêchent de le qualifier de tarif de production.

La charge de test observée vaut {test['observed_cost']:,.2f} EUR contre {test['predicted_cost']:,.2f} EUR prédits. O/P = {ratio:.4f}, soit une prédiction supérieure de {(1/ratio-1)*100:.2f} % à la charge observée. Intervalle d’échantillonnage bootstrap du ratio : [{ci[0]:.4f}, {ci[1]:.4f}] (300 réplications Poisson au niveau contrat). Cet intervalle ne représente ni une distribution prédictive de sinistres ni toute l’incertitude du modèle.

Aucun recalage sur le test n’est appliqué. Les seuils de contrôle proposés sont documentés dans acceptance.json ; ils ne sont pas revendiqués comme préenregistrés. Le test est désormais connu : tout nouveau réglage nécessite une nouvelle validation externe pour une approbation indépendante.

## Données et audit
Source originale CASdatasets, commit {report['source']['commit']}. {report['data_audit']['raw_policies']:,} contrats uniques et {report['data_audit']['raw_claims']:,} montants de sinistres. Aucun sinistre orphelin, aucune incohérence nombre/montants. Les tables ont été agrégées avant jointure ; l’exposition n’est pas dupliquée.

Les 1 224 expositions supérieures à un an sont conservées comme durées observées. Les 8 contrats avec plus de 4 sinistres sont conservés : aucune troncature arbitraire du nombre. Les gros sinistres sont conservés dans les objectifs d’évaluation ; la sévérité plafonnée à 100 000 EUR, avec recharge explicite des excédents, a été comparée comme modèle concurrent.

La source ne fournit pas de calendrier exploitable ou de liens longitudinaux fiables entre assurés. La séparation se fait par identifiant de contrat, sans garantie de regroupement par conducteur réel. La période est approximativement 2011–2013 selon la documentation. Aucune inflation, évolution de garanties ou actualisation du portefeuille n’est déduite de données absentes.

## Protocole d'estimation
Découpage stable SHA256 par contrat : train {train['policies']:,}, validation {val['policies']:,}, test {test['policies']:,}. Les sinistres suivent le découpage de leur contrat. Les bornes d’âge, de puissance et d’ancienneté sont définies explicitement, sans utiliser la cible. L’encodeur est ajusté sur train uniquement.

Variables : âge du conducteur et du véhicule par tranches, puissance fiscale par tranches, carburant, zone et région historique. Exclusion de BonusMalus pour éviter de réutiliser explicitement le même historique dans la mise à jour a posteriori. Les effets sont des associations tarifaires, pas des effets causaux.

- Fréquence : GLM Poisson, lien log ; nombre/exposition avec pondération par exposition, équivalent à un offset log(exposition). Trois pénalisations comparées sur validation. Alpha retenu : {model['selected_frequency']['alpha']}.
- Sévérité : GLM Gamma à lien log, sinistres positifs au niveau sinistre. Trois pénalisations, avec et sans plafond/recharge. Choix sur la déviance Tweedie de prime pure sur validation. Alpha retenu : {model['selected_severity']['alpha']}, plafond retenu : {model['selected_severity']['cap']}. Recalage multiplicatif de niveau estimé sur train uniquement : {model['selected_severity']['balance_multiplier']:.6f}.
- Les modèles restent ajustés sur train ; aucun réajustement sur validation ou test.

## Résultats hors échantillon
| Indicateur | Validation | Test |
|---|---:|---:|
| O/P nombre | {val['observed_predicted_count']:.4f} | {test['observed_predicted_count']:.4f} |
| O/P charge | {val['observed_predicted_cost']:.4f} | {ratio:.4f} |
| Déviance Poisson | {val['frequency_poisson_deviance']:.6f} | {test['frequency_poisson_deviance']:.6f} |
| Déviance Tweedie p=1,5 | {val['pure_tweedie_deviance_p15']:.6f} | {test['pure_tweedie_deviance_p15']:.6f} |
| Déviance Tweedie du tarif uniforme | {val['pure_baseline_deviance_p15']:.6f} | {test['pure_baseline_deviance_p15']:.6f} |

Le gain de déviance de prime pure sur test est de {gain:.2f} %. Ce faible gain de classement/ajustement ne compense pas le défaut de niveau agrégé. Les résultats par segment, y compris les mauvais résultats, sont dans test_segments.csv.

## Diagnostics de dispersion
Sur train, la dispersion de Pearson du Poisson vaut {report['dispersion_diagnostics']['poisson_pearson_phi']:.4f}. Le ratio résiduel rapporté à la variance NB2 vaut {report['dispersion_diagnostics']['nb2_pearson_residual_ratio']:.4f}, donc le mélange NB2 ne résout pas toute la surdispersion.

La forme Gamma estimée par vraisemblance, moyennes figées, vaut {report['dispersion_diagnostics']['gamma_shape_mle']:.4f} (dispersion {report['dispersion_diagnostics']['gamma_phi_mle']:.4f}). Le second moment relatif empirique vaut {report['dispersion_diagnostics']['gamma_empirical_relative_second_moment']:.4f}, très éloigné du moment impliqué par cette Gamma. Les 10 plus gros sinistres représentent {report['dispersion_diagnostics']['train_top10_claims_cost_share']*100:.2f} % de la charge d’apprentissage : l’hypothèse de queue Gamma mérite une revue.

## Personnalisation bayésienne
On pose U ~ Gamma(r,r), de moyenne 1, et N | U ~ Poisson(e × lambda(x) × U). La vraisemblance marginale binomiale négative est maximisée sur train, avec les moyennes du GLM figées : r = {model['frailty_shape_r']:.6f}.

Pour un profil inchangé : beta(x) = r/lambda(x), alpha = r. Après n sinistres et t années, fréquence ajustée = (r+n)/(r/lambda+t). Pour des profils historiques différents, il faudrait sommer leurs fréquences attendues pondérées par exposition ; cette V1 impose un risque comparable.

Ce r remplace le réglage illustratif beta=4. Son interprétation comme hétérogénéité persistante est une hypothèse : le panel annuel ne distingue pas une hétérogénéité durable d’une surdispersion transitoire. La performance de renouvellement n’est donc pas validée longitudinalement.

## Crédibilité sur les coûts
Faute de panel, les paramètres de Bühlmann ne sont pas estimés non paramétriquement. Une crédibilité **structurelle** est dérivée du même modèle collectif :

v(x) = lambda(x) × E[Y²|x] ; a(x) = lambda(x)² × m(x)² / r.

K(x) = r/lambda(x) × q, avec q = E[(Y/m(x))²] estimé sur train = {model['severity_second_moment_factor']:.6f}.

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
'''
 (ROOT/'reports/MODEL_CARD.md').write_text(text)
 # Synthetic profiles for tests only; no policy records or identifiers are published.
 fixtures=[]
 for age in [18,24,25,44,65,100]:
  for fuel in ['Diesel','Regular']:
   for area in ['A','F']:
    profile=dict(DrivAge=age,VehAge=7,VehPower=6,VehGas=fuel,Area=area,Region='Centre')
    fixtures.append({'profile':profile,'prediction':predict(profile,model)})
 (ROOT/'tests/profile_fixtures.json').write_text(json.dumps(fixtures,ensure_ascii=False,indent=2))
 print('Rapport, contrôles et 24 profils synthétiques générés.')
if __name__=='__main__':main()
