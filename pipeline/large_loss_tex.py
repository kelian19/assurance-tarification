"""Tableaux et figure de la note LaTeX pour l'étude des gros sinistres, générés depuis reports/large_loss.json.

python -m pipeline.large_loss_tex   (écrit docs/latex/tables_large_loss.tex et docs/latex/figures/fig_large_loss.pdf)
Aucune donnée individuelle n'est lue : seul le rapport versionné est utilisé.
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
FOREST,AMBER,MUTED,INK,LIGHT='#1F4E79','#B5651D','#65756A','#243C35','#9DB8D2'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.5,'axes.edgecolor':MUTED,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
                     'text.color':INK,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.bbox':'tight','legend.frameon':False})

def fr(x,d=2):
    t=f'{abs(x):,.{d}f}'.replace(',','\\,').replace('.','{,}')
    return ('$-$' if x<0 else '')+t
def macro(name,body):return f'\\newcommand{{\\{name}}}{{%\n{body}\n}}\n'
def tab(cols,header,rows):return '\\begin{tabular}{'+cols+'}\\toprule\n'+header+' \\\\\\midrule\n'+'\n'.join(r+' \\\\' for r in rows)+'\n\\bottomrule\\end{tabular}'

def main():
    r=json.loads((ROOT/'reports/large_loss.json').read_text(encoding='utf-8'));b=r['bootstrap'];g=r['gpd']
    out='% Fichier généré par python -m pipeline.large_loss_tex ; ne pas modifier à la main.\n'
    rows=[f"Test seul (niveau supposé connu) & {fr(b['test_only_interval95'][0],3)} & {fr(b['test_only_interval95'][1],3)} & non",
          f"Apprentissage et test (niveau recalé à chaque réplique) & {fr(b['full_interval95'][0],3)} & {fr(b['full_interval95'][1],3)} & \\textbf{{oui}}"]
    out+=macro('tabLLBootstrap',tab('lrrc',f"Bootstrap ({b['replicates']} répliques) & Borne basse & Borne haute & Contient 1",rows))
    out+=macro('llShareAboveOne',fr(100*b['share_replicates_op_at_least_1'],1)+'\\,\\%')
    out+=macro('llTestOP',fr(b['test_cost_op'],3))
    rows=[]
    for u,v in g.items():
        gl='infinie' if v['gpd_load_per_claim']==float('inf') else fr(v['gpd_load_per_claim'],0)
        iv='--' if not v['gpd_load_interval90'] else f"{fr(v['gpd_load_interval90'][0],0)}--{fr(v['gpd_load_interval90'][1],0)}"
        rows.append(f"{fr(float(u)/1000,0)}\\,k\\texteuro{{}} & {v['exceedances_train']} & {fr(v['xi'],2)} & {fr(v['empirical_load_per_claim'],0)} & {gl} & {iv} & {fr(100*v['share_infinite_mean_replicates'],0)}\\,\\%")
    out+=macro('tabLLGPD',tab('rrrrrrr','Seuil $u$ & Dépassements & $\\widehat\\xi$ & Excédent réalisé & Charge GPD & IC 90\\,\\% GPD & Répliques $\\xi\\geq1$',rows))
    rows=[f"{v['variant'].replace('€','\\texteuro{}')} & {fr(v['tail_per_claim'],0)} & {fr(v['validation_cost_op'],4)} & {fr(v['validation_tweedie_p15'],4)} & {fr(v['test_cost_op_descriptive'],4)}" for v in r['variants']]
    out+=macro('tabLLVariants',tab('lrrrr','Sévérité & Queue / sinistre & O/P validation & Tweedie validation & O/P test (descriptif)',rows))
    (ROOT/'docs/latex/tables_large_loss.tex').write_text(out,encoding='utf-8')
    # Figure : intervalles du ratio (gauche), charge de queue par seuil (droite)
    fig,(a,c)=plt.subplots(1,2,figsize=(7.2,2.6),gridspec_kw={'width_ratios':[1.1,1]})
    for y,(lo,hi),col,lab in ((1,b['test_only_interval95'],AMBER,'test seul'),(0,b['full_interval95'],FOREST,'apprentissage + test')):
        a.hlines(y,lo,hi,color=col,lw=7,alpha=.85);a.text(lo-0.01,y,lab,ha='right',va='center',fontsize=8,color=col)
    a.scatter([b['test_cost_op']]*2,[1,0],color='white',edgecolor=INK,zorder=3,s=30);a.axvline(1,color=INK,ls='--',lw=1)
    a.set_xlim(0.35,1.12);a.set_ylim(-0.7,1.7);a.set_yticks([]);a.spines['left'].set_visible(False);a.set_xlabel('O/P charge de test, intervalle bootstrap à 95 %')
    us=[float(u) for u in g];x=range(len(us))
    emp=[g[k]['empirical_load_per_claim'] for k in g];gp=[g[k]['gpd_load_per_claim'] for k in g]
    c.bar([i-0.18 for i in x],emp,width=0.36,color=LIGHT,label='excédent réalisé')
    c.bar([i+0.18 for i,v in zip(x,gp) if v!=float('inf')],[v for v in gp if v!=float('inf')],width=0.36,color=FOREST,label='GPD')
    for i,v in zip(x,gp):
        if v==float('inf'):c.text(i+0.18,50,'moyenne\ninfinie',ha='center',fontsize=7,color=AMBER)
    c.set_xticks(list(x));c.set_xticklabels([f'{int(u/1000)} k€' for u in us]);c.set_ylabel('charge de queue par sinistre (€)');c.legend(fontsize=7.5)
    fig.tight_layout();fig.savefig(ROOT/'docs/latex/figures/fig_large_loss.pdf');plt.close(fig);print('écrit tables_large_loss.tex et fig_large_loss.pdf')

if __name__=='__main__':main()
