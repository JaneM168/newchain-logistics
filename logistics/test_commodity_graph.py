import json
import unittest
from pathlib import Path
from commodity_graph import read_members, roles, stage_edges, STAGES

class CommodityTests(unittest.TestCase):
    def test_explicit_columns(self):
        rows={r['name']:r for r in read_members(Path(__file__).resolve().parents[1] / 'ccof_members.csv')}
        self.assertEqual(roles(rows['BZL LLC dba Sundays on Toro'],'coffee'), ['crop'])
        self.assertEqual(roles(rows['Cardiff Coffee Trading'],'coffee'), ['green_processing'])
        self.assertEqual(roles(rows['Blue Ridge Farms'],'pecan'), ['general_product'])
        self.assertNotIn('crop', roles(rows['Braga Organic Farms, Inc.'],'pecan'))
        self.assertEqual(roles(rows['Coffee Works, LLC'],'coffee'), ['green_processing','roasted'])
        self.assertEqual(roles(rows['Cypress Grove Chevre dba Cypress Grove'],'coffee'), [])
    def test_nearest_next_stage_and_self_exclusion(self):
        nodes=[dict(id='a',roles=['crop','green_processing'],latitude=0,longitude=0),dict(id='b',roles=['green_processing'],latitude=0,longitude=2),dict(id='c',roles=['green_processing'],latitude=0,longitude=1),dict(id='d',roles=['general_product'],latitude=0,longitude=.1)]
        edges,gaps=stage_edges(nodes, STAGES['coffee'],1)
        self.assertEqual(len(edges),1)
        self.assertEqual((edges[0]['source'],edges[0]['target']),('a','c'))
        self.assertTrue(any(g['reason']=='missing_target_stage' for g in gaps))
    def test_output(self):
        graphs=json.loads((Path(__file__).resolve().parents[1] / 'visualizations' / 'graphs.json').read_text())['graphs']
        for graph in graphs.values():
            nodes={n['id']:n for n in graph['nodes']}
            for e in graph['edges']:
                self.assertNotEqual(e['source'],e['target'])
                self.assertIn(e['from_stage'],nodes[e['source']]['roles'])
                self.assertIn(e['to_stage'],nodes[e['target']]['roles'])
                self.assertEqual(graph['stages'].index(e['to_stage'])-graph['stages'].index(e['from_stage']),1)
                eligible=[n for n in nodes.values() if e['to_stage'] in n['roles'] and n['latitude'] is not None and n['id']!=e['source']]
                from geo_utils import distance
                source=nodes[e['source']]
                ordered=sorted((distance((source['latitude'],source['longitude']),(n['latitude'],n['longitude'])),n['id']) for n in eligible)
                self.assertEqual(e['target'],ordered[e['rank']-1][1])
        self.assertEqual(graphs['coffee']['summary']['stage_counts']['crop'],1)
        self.assertEqual(len(graphs['pecan']['edges']),0)
        self.assertNotIn('crop',graphs['pecan']['summary']['stage_counts'])

if __name__=='__main__':
    unittest.main()
