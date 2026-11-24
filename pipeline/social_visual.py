"""Visuel 1080 × 1350 pour les réseaux, tiré des résultats versionnés (aucun chiffre saisi à la main).

python -m pipeline.social_visual      (écrit docs/social_tarification.png ; dépendance : matplotlib)
"""
import json
from pathlib import Path
from pipeline.social_card import render,fr,ACCENT,WARN,SOFT,SAND,INK,MUTED
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports'

def interval(ax,lo,hi,point,color,label):
    ax.axvline(1,color=INK,lw=1.2,ls='--');ax.text(1.008,0.62,'1 = juste',ha='left',fontsize=8,color=INK)
    ax.hlines(0,lo,hi,color=color,lw=9,alpha=.85);ax.scatter([point],[0],s=70,color='white',edgecolor=INK,zorder=3)
    ax.text(lo,-0.55,fr(lo,2),ha='center',fontsize=9,color=color);ax.text(hi,-0.55,fr(hi,2),ha='center',fontsize=9,color=color)
    ax.set_xlim(0.55,1.12);ax.set_ylim(-1,1);ax.set_yticks([]);ax.spines['left'].set_visible(False);ax.set_xlabel(label,fontsize=8)

def main():
    cal=json.loads((R/'calibration.json').read_text(encoding='utf-8'));lvl=json.loads((R/'level_diagnostic.json').read_text(encoding='utf-8'))
    ll=json.loads((R/'large_loss.json').read_text(encoding='utf-8'));test=cal['metrics'][2];bt=ll['bootstrap'];ls=lvl['largest_claim_sensitivity']
    cnt,cost=test['observed_predicted_count'],test['observed_predicted_cost'];xi=ll['gpd']['100000']['xi']
    def constat(ax):
        ax.barh([1,0],[cnt,cost],color=[ACCENT,WARN],height=0.55);ax.axvline(1,color=INK,lw=1.2,ls='--')
        ax.set_yticks([1,0]);ax.set_yticklabels(['nombre','charge'],fontsize=9);ax.set_xlim(0.6,1.08)
        for y_,v in ((1,cnt),(0,cost)):ax.text(v-0.01,y_,fr(v,3),ha='right',va='center',fontsize=10,color='white',weight='bold')
        ax.set_xlabel('observé / prédit sur le test',fontsize=8)
    cards=[('Le constat',f'{fr(test["policies"])} contrats test :\nfréquence juste, charge non',('draw',constat)),
           ('Le suspect',f'Un seul sinistre d’apprentissage :\n{fr(100*ls["largest_share_of_train_cost"],1)} % de la charge',('big',f'{fr(ls["largest_train_claim"]/1e6,2)} M€',WARN,40)),
           ('Le piège','Bootstrap du test seul :\n« le modèle est biaisé »',('draw',lambda ax:interval(ax,*bt['test_only_interval95'],cost,WARN,'intervalle à 95 %, test seul'))),
           ('Le bon calcul','Apprentissage et test\nrééchantillonnés ensemble',('draw',lambda ax:interval(ax,*bt['full_interval95'],cost,ACCENT,'intervalle à 95 %, bootstrap complet'))),
           ('La raison','Queue de Pareto très lourde :\nla charge observée est souvent sous l’espérance',('big',f'ξ ≈ {fr(xi,2)}',ACCENT,40)),
           ('La décision','Pas de recalage sur du bruit :\nécart documenté',('big','Modèle conservé',ACCENT,28))]
    lo,hi=bt['full_interval95']
    render(ROOT/'docs/social_tarification.png','TARIFICATION AUTOMOBILE · freMTPL2',f'Mon modèle surestime\nla charge de {fr(100*(1/cost-1))} %.','Biais du modèle ou hasard des gros sinistres ?',cards,
           f'IC 95 % du ratio : [{fr(lo,2)} ; {fr(hi,2)}], qui contient 1',
           'GLM fréquence et coût · théorie des valeurs extrêmes  ·  github.com/kelian19/assurance-tarification')

if __name__=='__main__':main()
