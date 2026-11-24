"""Pourquoi la charge test est-elle surestimée ? Diagnostic du niveau de sévérité à partir des seuls agrégats versionnés.

Le bootstrap publié (reports/calibration.json) ne rééchantillonne que le test : il traite le niveau prédit comme connu.
Or ce niveau est appris sur train, où un très petit nombre de sinistres pèse lourd (le plus gros : 10,8 % de la charge).
Le modèle étant équilibré sur train (recalage multiplicatif), un sinistre extrême de train relève le niveau prédit partout.

Deux mesures, sans réajustement ni nouvelle lecture du test :
1. sensibilité : niveau prédit si le plus gros sinistre de train n'avait pas été tiré (équilibrage sur la charge sans lui) ;
2. incertitude d'estimation du niveau : erreur-type relative de la moyenne de sévérité de train, √((q − 1)/n), avec
   q = E[(Y/μ̂)²] le second moment relatif publié, et de la fréquence, √(φ/N) ; combinée à l'erreur d'échantillonnage du test
   (déduite de l'intervalle bootstrap publié) en échelle logarithmique. Approximation normale : avec une queue aussi lourde,
   la loi de la moyenne est asymétrique ; l'intervalle obtenu est un ordre de grandeur, pas une garantie de couverture.

python -m pipeline.level_diagnostic   (écrit reports/level_diagnostic.json)
"""
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
Z95=1.959963984540054

def level_diagnostic(report):
    train,val,test=report['metrics'];disp=report['dispersion_diagnostics']
    n=train['claims'];cost=train['observed_cost'];largest=report['data_audit']['maximum_claim'];share=disp['train_largest_claim_cost_share']
    if abs(largest/cost-share)>1e-6:raise ValueError('Le plus gros sinistre n’est pas dans train : la sensibilité ne s’applique pas.')
    # 1. Sensibilité au plus gros sinistre : moyenne de sévérité de train sans lui, rapportée à la moyenne avec lui.
    factor=((cost-largest)/(n-1))/(cost/n)
    sens={'largest_train_claim':largest,'largest_share_of_train_cost':share,'top10_share_of_train_cost':disp['train_top10_claims_cost_share'],
          'level_factor_without_largest':factor,
          'validation_cost_op_without_largest':val['observed_predicted_cost']/factor,'test_cost_op_without_largest':test['observed_predicted_cost']/factor}
    # 2. Incertitude du niveau appris sur train, combinée à l'échantillonnage du test.
    q=disp['gamma_empirical_relative_second_moment'];phi=disp['poisson_pearson_phi']
    se_sev=math.sqrt((q-1)/n);se_freq=math.sqrt(phi/n);se_level=math.hypot(se_sev,se_freq)
    lo,hi=report['test_aggregate_cost_op_bootstrap95'];se_test=(math.log(hi)-math.log(lo))/(2*Z95)
    se=math.hypot(se_level,se_test);r=test['observed_predicted_cost'];z=math.log(r)/se
    unc={'relative_se_train_severity_mean':se_sev,'relative_se_train_frequency':se_freq,'relative_se_train_level':se_level,
         'log_se_test_sampling_from_bootstrap':se_test,'log_se_combined':se,
         'test_cost_op':r,'test_only_interval95':[lo,hi],'combined_interval95':[r*math.exp(-Z95*se),r*math.exp(Z95*se)],'z_score':z,
         'p_value_two_sided_normal':math.erfc(abs(z)/math.sqrt(2))}
    return {'largest_claim_sensitivity':sens,'level_uncertainty':unc,
            'reading':['Le test seul ne mesure pas l’incertitude du niveau appris : celle-ci vient de quelques gros sinistres de train.',
                       'Sans le plus gros sinistre de train, le niveau prédit baisserait d’environ 11 % : il explique à lui seul plus de la moitié de l’écart test, et la validation passerait en sous-estimation : le vrai niveau est entre les deux.',
                       'Même en ajoutant l’incertitude du niveau appris, l’intervalle reste sous 1 : une part de la surestimation n’est pas du bruit.',
                       'Correction à évaluer (exige les données et un nouvel échantillon indépendant) : charge des gros sinistres estimée par un modèle de queue (GPD) plutôt que par l’excédent réalisé sur train.'],
            'method':'Agrégats versionnés de reports/calibration.json ; aucun réajustement, aucune nouvelle lecture du test ; approximation normale en log.'}

def main():
    report=json.loads((ROOT/'reports/calibration.json').read_text(encoding='utf-8'));out=level_diagnostic(report)
    (ROOT/'reports/level_diagnostic.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=1))

if __name__=='__main__':main()
