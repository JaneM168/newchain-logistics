import json
import textwrap
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

root=Path(__file__).resolve().parents[1] / 'visualizations'
bundle=json.loads((root/'graphs.json').read_text())
colors=bundle['colors']
names={'crop':'COFFEE GROWERS','green_coffee':'GREEN COFFEE PRODUCT', 'processing_unspecified':'PROCESSING: STAGE UNKNOWN','roasted':'ROASTED COFFEE PRODUCT','general_product':'GENERAL COFFEE'}
fig=plt.figure(figsize=(28,16),facecolor='#f5f7fb')
ax=fig.add_axes([.025,.29,.95,.58]);ax.set_xlim(-.15,4.95);ax.set_ylim(-.8,17.6);ax.axis('off')
fig.text(.04,.957,'Coffee & pecan logistics networks',fontsize=28,weight='bold',color='#182b43')
fig.text(.04,.927,f"K = {bundle['k']} nearest next-stage businesses • unknown processing has no flow edges • products do not prove in-house operations",fontsize=14,color='#41556f')
g=bundle['graphs']['coffee'];positions={};display_stages=g.get('display_stages',g['stages']);cols={s:i for i,s in enumerate(display_stages)}
for s in display_stages:
 i=cols[s];ns=sorted([n for n in g['nodes'] if s in n['roles']],key=lambda n:n['name'].casefold())
 ax.text(i,17.3,names[s],fontsize=12,weight='bold',color=colors[s])
 ax.text(i,16.8,f'{len(ns)} businesses',fontsize=10,color='#52647a')
 for j,n in enumerate(ns):
  y=15.7-j*.95
  positions[n['id']+'|'+s]=(i,y)
for e in g['edges']:
 a=positions[e['source']+'|'+e['from_stage']];b=positions[e['target']+'|'+e['to_stage']]
 ax.add_patch(FancyArrowPatch((a[0]+.015,a[1]),(b[0]-.025,b[1]),arrowstyle='-|>',mutation_scale=9,linewidth=.8,color='#8b9cb3',alpha=.23,connectionstyle='arc3,rad=0.035',zorder=1))
for n in g['nodes']:
 for s in n['roles']:
  x,y=positions[n['id']+'|'+s];unlocated=n['latitude'] is None
  ax.scatter([x],[y],s=100,facecolors='white' if unlocated else colors[s],edgecolors=colors[s],linewidths=2,zorder=3)
  name=n['name']
  if len(name)>39:name=name[:37]+'…'
  ax.text(x+.045,y+.10,name+(' *' if unlocated else ''),fontsize=8.7,color='#20324b',zorder=4,bbox=dict(facecolor='#f5f7fb',edgecolor='none',alpha=.9,pad=.4))
fig.text(.04,.273,f"COFFEE  ·  {g['summary']['businesses']} unique businesses  ·  {g['summary']['located']} city-located  ·  {len(g['edges'])} directed links",fontsize=13,weight='bold',color='#20324b')
fig.text(.04,.247,'A business can appear in several stages. Hollow nodes (*) lack coordinates and have no distance-based links.',fontsize=11,color='#52647a')
# Pecan panel: honest empty source stage rather than invented edges.
pax=fig.add_axes([.04,.075,.92,.145]);pax.set_xlim(0,1);pax.set_ylim(0,1);pax.axis('off')
pax.text(0,.95,'PECAN GROWERS',color=colors['crop'],weight='bold',fontsize=12)
pax.text(.43,.95,'PECAN PRODUCTS / SERVICES',color=colors['general_product'],weight='bold',fontsize=12)
pax.text(0,.64,'No explicit pecan crop records',fontsize=12,color='#53647b')
pax.text(0,.45,'No grower-to-product links created',fontsize=11,color='#8b610b')
p=bundle['graphs']['pecan']
for j,n in enumerate(sorted(p['nodes'],key=lambda n:n['name'])):
 y=.76-j*.14
 pax.scatter([.43],[y],s=65,facecolors='white' if n['latitude'] is None else colors['general_product'],edgecolors=colors['general_product'],linewidths=1.8)
 pax.text(.45,y,n['name']+(' *' if n['latitude'] is None else ''),va='center',fontsize=10,color='#20324b')
fig.text(.04,.035,'Location basis: approximate GeoNames city points, not verified farm sites or driving distances. Same-city ties sort by business URL.',fontsize=10,color='#52647a')
fig.savefig(root/'commodity_networks.png',dpi=170,facecolor=fig.get_facecolor())
fig.savefig(root/'commodity_networks.svg',facecolor=fig.get_facecolor())
print(root/'commodity_networks.png')

svg_path=root/'commodity_networks.svg'
svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text().splitlines())+'\n')
