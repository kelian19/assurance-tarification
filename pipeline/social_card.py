"""Mise en page d'un visuel portrait 1080 × 1350 pour les réseaux : titre, six cartes numérotées, résultat en pied de page.

Chaque carte : (titre, texte, contenu) ; contenu = ('draw', fonction(ax)) pour une mini-figure, ou ('big', texte, couleur)
pour un chiffre clé. Couleurs du projet (vert, brique, crème).
"""
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
INK='#1c2b27';MUTED='#6a7a72';PAPER='#fbfaf6';ACCENT='#174f43';WARN='#b24a3a';SOFT='#a9c9a3';SAND='#e8dcc4'
plt.rcParams.update({'font.family':'DejaVu Sans','axes.edgecolor':MUTED,'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED})

def fr(x,d=0):
    return f'{x:,.{d}f}'.replace(',',' ').replace('.',',') if d else f'{x:,.0f}'.replace(',',' ')

def clean(ax):
    for s in ('top','right'):ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8,length=2);ax.set_facecolor('white')

def render(out,kicker,title,subtitle,cards,big,small):
    fig=plt.figure(figsize=(10.8,13.5),dpi=100);fig.patch.set_facecolor(PAPER)
    fig.text(0.06,0.955,kicker,fontsize=15,weight='bold',color=WARN,va='top')
    fig.text(0.06,0.925,title,fontsize=36,weight='bold',color=ACCENT,va='top',linespacing=1.05)
    fig.text(0.06,0.818,subtitle,fontsize=17,color=MUTED,va='top')
    W,H=0.425,0.205;xs=[0.05,0.525];ys=[0.565,0.345,0.125]
    for k,(head,text,content) in enumerate(cards):
        x=xs[k%2];y=ys[k//2]
        card=fig.add_axes([x,y,W,H]);card.set_axis_off();card.set_xlim(0,1);card.set_ylim(0,1)
        card.add_patch(FancyBboxPatch((0,0),1,1,boxstyle='round,pad=0,rounding_size=0.06',fc='white',ec='#e2e0d6',lw=1.2,transform=card.transAxes,clip_on=False))
        card.text(0.075,0.875,str(k+1),ha='center',va='center',fontsize=16,weight='bold',color='white',bbox=dict(boxstyle='circle,pad=0.38',fc=ACCENT,ec='none'))
        card.text(0.18,0.885,head,ha='left',va='center',fontsize=17,weight='bold',color=INK)
        card.text(0.05,0.76,text,ha='left',va='top',fontsize=12,color=MUTED,linespacing=1.2)
        if content[0]=='draw':
            ax=fig.add_axes([x+0.06,y+0.028,W-0.09,H*0.46]);clean(ax);content[1](ax)
        else:
            card.text(0.5,0.25,content[1],ha='center',va='center',fontsize=content[3] if len(content)>3 else 34,weight='bold',color=content[2])
    fig.text(0.06,0.083,big,fontsize=27,weight='bold',color=INK,va='top')
    fig.text(0.06,0.040,small,fontsize=13.5,color=MUTED,va='top')
    fig.savefig(out,dpi=100,facecolor=PAPER);plt.close(fig);print('écrit',out)
