"""Figures vectorielles de la note LaTeX, tirées des rapports versionnés et du moteur de prime.

    python -m pipeline.make_figures

Aucune donnée individuelle n'est nécessaire : les figures lisent reports/*.json, reports/test_segments.csv
et artifacts/model.json. L'exemple chiffré de la note (profil de 45 ans) est rejoué avec python/pricing.py
et comparé aux montants imprimés dans la note.
Sorties : docs/latex/figures/*.pdf.
"""
import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from python.model import predict  # noqa: E402
from python.pricing import Period, calculate  # noqa: E402

OUT = ROOT / 'docs/latex/figures'
FOREST, AMBER, MUTED, INK = '#1F4E79', '#B5651D', '#65756A', '#243C35'
LIGHT, MID = '#9DB8D2', '#5B87B0'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 8.5, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK,
    'xtick.color': INK, 'ytick.color': INK, 'text.color': INK, 'axes.spines.top': False,
    'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#DDE3EA', 'grid.linewidth': .5,
    'axes.axisbelow': True, 'pdf.fonttype': 42, 'savefig.bbox': 'tight', 'legend.frameon': False,
})


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def pct(x, _=None):
    return f'{x:g}'.replace('.', ',')


def fig_calibration(cal):
    """Observé/prédit par échantillon, et charge totale en M€."""
    metrics = {m['sample']: m for m in cal['metrics']}
    names = ['train', 'validation', 'test']
    labels = ['Apprentissage', 'Validation', 'Test']
    lo, hi = cal['test_aggregate_cost_op_bootstrap95'][0] if isinstance(cal['test_aggregate_cost_op_bootstrap95'][0], list) else cal['test_aggregate_cost_op_bootstrap95']
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.1, 2.9), gridspec_kw={'width_ratios': [1.25, 1]})
    x = np.arange(3)
    w = .34
    count = np.array([metrics[n]['observed_predicted_count'] for n in names]) * 100
    cost = np.array([metrics[n]['observed_predicted_cost'] for n in names]) * 100
    a.bar(x - w / 2, count, w, color=LIGHT, zorder=3, label='nombre de sinistres')
    a.bar(x + w / 2, cost, w, color=FOREST, zorder=3, label='charge')
    a.errorbar([2 + w / 2], [cost[2]], yerr=[[cost[2] - lo * 100], [hi * 100 - cost[2]]], fmt='none', ecolor=AMBER, elinewidth=1.5, capsize=3, zorder=5,
               label='IC bootstrap 95 % (test, 300 réplicats)')
    for xi, v in zip(x - w / 2, count):
        a.text(xi, v + 1.5, pct(round(v, 1)), ha='center', fontsize=7)
    for xi, v in zip(x + w / 2, cost):
        a.text(xi - .02, 3, pct(round(v, 1)), ha='center', fontsize=7, color='white', fontweight='bold')
    a.axhline(100, color=INK, lw=1, zorder=4)
    a.set_xticks(x)
    a.set_xticklabels(labels)
    a.set_ylim(0, 128)
    a.set_ylabel('observé / prédit (%)')
    a.legend(loc='upper center', bbox_to_anchor=(.5, 1.22), ncol=1, fontsize=7)
    a.set_title('Calibration agrégée', loc='left', fontsize=9, fontweight='bold', color=FOREST, pad=30)
    obs = np.array([metrics[n]['observed_cost'] for n in names]) / 1e6
    pred = np.array([metrics[n]['predicted_cost'] for n in names]) / 1e6
    b.bar(x - w / 2, obs, w, color=AMBER, zorder=3, label='observée')
    b.bar(x + w / 2, pred, w, color=FOREST, zorder=3, label='prédite')
    for xi, v in zip(x - w / 2, obs):
        b.text(xi, v + .5, f'{v:.1f}'.replace('.', ','), ha='center', fontsize=7)
    for xi, v in zip(x + w / 2, pred):
        b.text(xi, v + .5, f'{v:.1f}'.replace('.', ','), ha='center', fontsize=7)
    b.set_xticks(x)
    b.set_xticklabels(['Appr.', 'Valid.', 'Test'])
    b.set_ylim(0, 44)
    b.set_ylabel('charge totale (M€)')
    b.legend(loc='upper right', fontsize=7)
    b.set_title('Charge totale', loc='left', fontsize=9, fontweight='bold', color=FOREST, pad=30)
    fig.tight_layout(w_pad=2)
    return fig


def fig_segments():
    """O/P du nombre et de la charge par segment du test ; surface ∝ exposition."""
    rows = list(csv.DictReader((ROOT / 'reports/test_segments.csv').open(encoding='utf-8')))
    groups = [('DrivAgeBand', "Âge du conducteur"), ('Area', 'Zone'), ('Region', 'Région')]
    counts = [sum(r['feature'] == g for r in rows) for g, _ in groups]
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 5.3), gridspec_kw={'width_ratios': [1, 1, 1.15]})
    expo_max = max(float(r['exposure']) for r in rows)
    for ax, (feature, title), n in zip(axes, groups, counts):
        part = [r for r in rows if r['feature'] == feature]
        y = np.arange(len(part))[::-1]
        size = [10 + 70 * float(r['exposure']) / expo_max for r in part]
        ax.axvline(1, color=INK, lw=1, zorder=2)
        cap = 2.3  # valeurs au-delà : tronquées à la marge et annotées (jamais masquées)
        counts_op = [min(float(r['count_op']), cap) for r in part]
        costs_op = [min(float(r['cost_op']), cap) for r in part]
        ax.scatter(counts_op, y, s=size, facecolor='white', edgecolor=MID, lw=1.2, zorder=4, label='nombre')
        ax.scatter(costs_op, y, s=size, color=FOREST, alpha=.9, lw=0, zorder=5, label='charge')
        for yi, r, c1, c2 in zip(y, part, counts_op, costs_op):
            ax.plot([c1, c2], [yi, yi], color=LIGHT, lw=.9, zorder=3)
            if float(r['cost_op']) > cap:
                ax.annotate(f"{float(r['cost_op']):.1f}".replace('.', ',') + ' →', (cap, yi), xytext=(-4, 5), textcoords='offset points', ha='right', fontsize=6.5, color=FOREST)
        ax.set_yticks(y)
        ax.set_yticklabels([r['segment'].replace('Provence-Alpes-Cotes-D\'Azur', 'PACA').replace('Languedoc-Roussillon', 'Languedoc-R.').replace('Nord-Pas-de-Calais', 'Nord-PdC') for r in part], fontsize=6.6 if feature == 'Region' else 7.5)
        ax.set_xlim(0, 2.4)
        ax.set_xlabel('observé / prédit')
        ax.set_title(title, loc='left', fontsize=9, fontweight='bold', color=FOREST)
        ax.grid(axis='y', alpha=0)
    axes[0].legend(loc='lower left', fontsize=7, bbox_to_anchor=(0, 1.08), ncol=2) if False else None
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='upper center', ncol=2, fontsize=7.5, bbox_to_anchor=(.5, 1.03), markerscale=1.2)
    fig.tight_layout(w_pad=1.2)
    return fig


def fig_diagnostics(cal, nb):
    """Poisson vs NB2 (écarts relatifs) et sensibilité aux gros sinistres."""
    val = {m['model']: m for m in nb['metrics'] if m['sample'] == 'validation'}
    test = {m['model']: m for m in nb['metrics'] if m['sample'] == 'test'}
    items = [
        ('log-vraisemblance négative\n(validation)', 100 * (val['NB2']['negative_log_likelihood_per_policy'] / val['Poisson']['negative_log_likelihood_per_policy'] - 1), 'meilleur si < 0'),
        ('O/P charge\n(test déjà consulté)', 100 * (test['NB2']['observed_predicted_cost'] - test['Poisson']['observed_predicted_cost']), 'points'),
        ('déviance Tweedie prime pure\n(test déjà consulté)', 100 * (test['NB2']['tweedie_deviance_pure_p15'] / test['Poisson']['tweedie_deviance_pure_p15'] - 1), 'meilleur si < 0'),
    ]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.1, 2.6), gridspec_kw={'width_ratios': [1.35, 1]})
    y = np.arange(len(items))[::-1]
    vals = [v for _, v, _ in items]
    a.barh(y, vals, color=[FOREST if v < 0 else AMBER for v in vals], height=.55, zorder=3)
    a.axvline(0, color=INK, lw=1)
    for yi, v in zip(y, vals):
        a.text(v + (.02 if v >= 0 else -.02), yi, f'{v:+.2f}'.replace('.', ','), va='center', ha='left' if v >= 0 else 'right', fontsize=7.5)
    a.set_yticks(y)
    a.set_yticklabels([i[0] for i in items], fontsize=7.5)
    a.set_xlim(-1.2, 1.2)
    a.set_xlabel('NB2 relativement à Poisson (%, ou points pour O/P)')
    a.set_title('Poisson ou NB2 : écarts mesurés', loc='left', fontsize=9, fontweight='bold', color=FOREST)
    sens = cal['large_claim_sensitivity']
    xs = np.arange(len(sens))
    b.bar(xs, [s['train_tail_per_claim'] for s in sens], color=MID, width=.55, zorder=3)
    for xi, s in zip(xs, sens):
        b.text(xi, s['train_tail_per_claim'] + 12, f"{s['train_claims_above']} sin.", ha='center', fontsize=7)
    b.set_xticks(xs)
    b.set_xticklabels([f"> {s['threshold'] // 1000} k€" for s in sens])
    b.set_ylabel('excédent moyen par sinistre (€)')
    b.set_ylim(0, 720)
    b.set_title('Poids des gros sinistres', loc='left', fontsize=9, fontweight='bold', color=FOREST)
    fig.tight_layout(w_pad=2)
    return fig


def fig_personalisation(model):
    """Prime annuelle d'un profil selon l'historique saisi : bayésienne, crédibilité, tarif initial."""
    profile = {'DrivAge': 45, 'VehAge': 7, 'VehPower': 6, 'VehGas': 'Diesel', 'Area': 'C', 'Region': 'Centre'}
    p = predict(profile, model)
    years = np.arange(0, 11)

    def premium(method, t, n, amount=0.):
        # t années entières ; les n sinistres sont répartis un par année (montant total réparti également).
        history = [Period(1., 1 if i < n else 0, amount / n if i < n else 0.) for i in range(t)]
        return calculate(p['frequency'], p['severity'], history, beta=p['beta'], k=p['k'], method=method)['annual_pure']

    prior = p['prior']
    # Contrôle contre les montants imprimés dans la note.
    three = calculate(p['frequency'], p['severity'], [Period(1., 0)] * 3, beta=p['beta'], k=p['k'], method='bayes')
    assert abs(prior - 157.84) < .005 and abs(three['bayes'] - 117.27) < .005 and abs(three['credibility'] - 156.05) < .005
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.1, 2.9))
    a.plot(years, [premium('bayes', t, 0) for t in years], color=FOREST, lw=2, marker='o', ms=3.5, label='bayésienne (fréquence)')
    a.plot(years, [premium('credibility', t, 0) for t in years], color=AMBER, lw=2, marker='s', ms=3.5, label='crédibilité structurelle')
    a.axhline(prior, color=INK, lw=1, ls='--', label=f"tarif initial ({prior:.2f}".replace('.', ',') + ' €)')
    a.set_xlabel('années assurées sans sinistre')
    a.set_ylabel('prime pure annuelle (€)')
    a.set_ylim(0, 190)
    a.legend(loc='lower left', fontsize=7)
    a.set_title('Historique sans sinistre', loc='left', fontsize=9, fontweight='bold', color=FOREST)
    t = 3
    ns = np.arange(0, 4)
    amounts = [0., 1500., 3000., 4500.]
    bayes = [premium('bayes', t, n, a_) for n, a_ in zip(ns, amounts)]
    cred = [premium('credibility', t, n, a_) for n, a_ in zip(ns, amounts)]
    w = .36
    b.bar(ns - w / 2, bayes, w, color=FOREST, zorder=3, label='bayésienne')
    b.bar(ns + w / 2, cred, w, color=AMBER, zorder=3, label='crédibilité')
    b.axhline(prior, color=INK, lw=1, ls='--')
    for xi, v in zip(ns - w / 2, bayes):
        b.text(xi, v + 5, f'{v:.0f}', ha='center', fontsize=7)
    for xi, v in zip(ns + w / 2, cred):
        b.text(xi, v + 5, f'{v:.0f}', ha='center', fontsize=7)
    b.set_xticks(ns)
    b.set_xlabel('sinistres sur 3 ans (coût fictif 1 500 € chacun)')
    b.set_ylim(0, 640)
    b.legend(loc='upper left', fontsize=7)
    b.set_title('Trois années observées', loc='left', fontsize=9, fontweight='bold', color=FOREST)
    fig.tight_layout(w_pad=2)
    return fig


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cal, nb, model = load('reports/calibration.json'), load('reports/poisson_vs_nb.json'), load('artifacts/model.json')
    figures = {'fig_calibration': fig_calibration(cal), 'fig_segments': fig_segments(), 'fig_diagnostics': fig_diagnostics(cal, nb),
               'fig_personalisation': fig_personalisation(model)}
    for name, fig in figures.items():
        fig.savefig(OUT / f'{name}.pdf')
        plt.close(fig)
        print('écrit', name)


if __name__ == '__main__':
    main()
