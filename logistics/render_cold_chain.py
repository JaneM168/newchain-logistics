"""Render cold-chain commodity overview and per-commodity labeled networks."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1] / 'visualizations'
BACKGROUND = '#f5f7fb'


def draw(ax, graph, colors, labeled=False):
    ax.set_xlim(-.12, 1.95 if labeled else 1.12)
    ax.set_ylim(-.09, 1.15)
    ax.axis('off')
    positions = {}
    for x, stage in enumerate(graph['stages']):
        nodes = sorted((n for n in graph['nodes'] if stage in n['roles']), key=lambda n:n['name'].casefold())
        ax.text(x, 1.08, ('GROWERS' if stage == 'crop' else 'PRODUCTS / SERVICES') + f' ({len(nodes)})',
                color=colors[stage], fontsize=10, weight='bold', ha='left' if labeled else 'center')
        for i, node in enumerate(nodes):
            positions[(node['id'], stage)] = (x, 1 - i / max(1, len(nodes)-1))
    for edge in graph['edges']:
        a=positions[(edge['source'],edge['from_stage'])]
        b=positions[(edge['target'],edge['to_stage'])]
        ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=6,
                                    color='#8496af',alpha=.22,linewidth=.6,zorder=1))
    for node in graph['nodes']:
        for stage in node['roles']:
            x,y=positions[(node['id'],stage)]
            ax.scatter([x],[y],s=38 if labeled else 28,facecolors='white' if node['latitude'] is None else colors[stage],
                       edgecolors=colors[stage],linewidths=1.3,zorder=3)
            if labeled:
                label=node['name']
                if len(label)>55:
                    label=label[:53]+'…'
                ax.text(x+.025,y,label+(' *' if node['latitude'] is None else ''),fontsize=8,va='center',
                        color='#23334b',zorder=4,bbox=dict(facecolor=BACKGROUND,edgecolor='none',alpha=.9,pad=.2))


def main():
    bundle=json.loads((ROOT/'graphs.json').read_text())
    fig,axes=plt.subplots(3,2,figsize=(15,19),facecolor=BACKGROUND)
    fig.subplots_adjust(left=.06,right=.94,top=.84,bottom=.09,wspace=.27,hspace=.4)
    fig.suptitle('Cold-chain commodity networks',x=.06,y=.975,ha='left',fontsize=28,weight='bold',color='#20324b')
    fig.text(.06,.94,f"K = {bundle['k']} nearest next-stage businesses • crop growers → products / services",fontsize=13,color='#52647a')
    fig.text(.06,.915,'Green = grower    Purple = product / service    Hollow = location unresolved',fontsize=12,color='#52647a')
    for ax,commodity in zip(axes.flat,bundle['cold_commodities']):
        graph=bundle['graphs'][commodity]
        summary=graph['summary']
        draw(ax,graph,bundle['colors'])
        ax.set_title(f"{commodity.capitalize()}\n{summary['businesses']} businesses · {summary['edges']} links · {summary['unresolved']} unlocated",
                     fontsize=13,loc='left',pad=37,color='#20324b',weight='bold')
        max_rows=max(summary['stage_counts'].values(),default=1)
        single,sax=plt.subplots(figsize=(19,max(6,max_rows*.3+2)),facecolor=BACKGROUND)
        single.subplots_adjust(left=.03,right=.98,top=.88,bottom=.1)
        draw(sax,graph,bundle['colors'],labeled=True)
        single.suptitle(f"{commodity.capitalize()} · K={bundle['k']} · {summary['businesses']} businesses · {summary['edges']} links",fontsize=20,weight='bold',color='#20324b')
        single.text(.04,.035,'Approximate city locations. * = unresolved. Roles can overlap; links are candidates, not confirmed trade.',fontsize=10,color='#52647a')
        single.savefig(ROOT/(commodity+'_network.png'),dpi=150,facecolor=BACKGROUND)
        single.savefig(ROOT/(commodity+'_network.svg'),facecolor=BACKGROUND)
        plt.close(single)
    fig.text(.06,.055,'City-level coordinates, not verified production sites or driving distances. Same-city ties sort by business URL.',fontsize=11,color='#52647a')
    fig.text(.06,.035,'Roles can overlap. No maximum-distance cutoff. These links do not establish actual trade or cold-storage capacity.',fontsize=11,color='#52647a')
    fig.savefig(ROOT/'cold_chain_networks.png',dpi=160,facecolor=BACKGROUND)
    fig.savefig(ROOT/'cold_chain_networks.svg',facecolor=BACKGROUND)
    plt.close(fig)
    print(ROOT/'cold_chain_networks.png')

if __name__ == '__main__':
    main()
