import json
import unittest
from pathlib import Path
from commodity_graph import read_members, roles, stage_edges, STAGES, related_labels

class CommodityTests(unittest.TestCase):
    def test_explicit_columns(self):
        rows={r['name']:r for r in read_members(Path(__file__).resolve().parents[1] / 'ccof_members.csv')}
        self.assertEqual(roles(rows['BZL LLC dba Sundays on Toro'],'coffee'), ['crop'])
        self.assertEqual(roles(rows['Cardiff Coffee Trading'],'coffee'), ['green_coffee'])
        self.assertEqual(roles(rows['Blue Ridge Farms'],'pecan'), ['general_product'])
        self.assertNotIn('crop', roles(rows['Braga Organic Farms, Inc.'],'pecan'))
        self.assertEqual(roles(rows['Coffee Works, LLC'],'coffee'), ['roasted','processing_unspecified'])
        self.assertEqual(roles(rows['Cypress Grove Chevre dba Cypress Grove'],'coffee'), [])
    def test_nearest_next_stage_and_self_exclusion(self):
        nodes=[dict(id='a',roles=['crop','green_coffee'],latitude=0,longitude=0),dict(id='b',roles=['green_coffee'],latitude=0,longitude=2),dict(id='c',roles=['green_coffee'],latitude=0,longitude=1),dict(id='d',roles=['general_product'],latitude=0,longitude=.1)]
        edges,gaps=stage_edges(nodes, STAGES['coffee'],1)
        self.assertEqual(len(edges),1)
        self.assertEqual((edges[0]['source'],edges[0]['target']),('a','c'))
        self.assertTrue(any(g['reason']=='missing_target_stage' for g in gaps))
    def test_processing_does_not_imply_green_or_roasting(self):
        row=dict(crop_labels='',product_service_labels='Coffee Processing')
        self.assertEqual(roles(row,'coffee'),['processing_unspecified'])
        row['product_service_labels']='Coffee (Green) ; Coffee Processing'
        self.assertEqual(roles(row,'coffee'),['green_coffee','processing_unspecified'])
        nodes=[dict(id='grower',roles=['crop'],latitude=0,longitude=0),
               dict(id='processor',roles=['processing_unspecified'],latitude=0,longitude=1)]
        edges,gaps=stage_edges(nodes,STAGES['coffee'],5)
        self.assertEqual(edges,[])
        graph=json.loads((Path(__file__).resolve().parents[1]/'visualizations'/'coffee.json').read_text())
        self.assertEqual(sum('processing_unspecified' in n['roles'] for n in graph['nodes']),3)
        self.assertEqual(sum('green_coffee' in n['roles'] for n in graph['nodes']),2)
        self.assertFalse(any('processing_unspecified' in [e['from_stage'],e['to_stage']] for e in graph['edges']))
    def test_cold_chain_aliases_and_exclusions(self):
        cases=[('blackberry','Blackberries','Blackberry'),
               ('grapefruit','Grapefruit','Grapefruit'),
               ('pear','Asian Pears','Pear Packing (Client Profile Products only)'),
               ('celery','Celery','Celery Hearts'),
               ('cucumber','Cucumbers','Cucumbers'),
               ('asparagus','Asparagus','Asparagus')]
        for commodity,crop,product in cases:
            with self.subTest(commodity=commodity):
                row=dict(crop_labels=crop,product_service_labels=product,ambiguous_labels='')
                self.assertEqual(roles(row,commodity),['crop','general_product'])
        for commodity,term in [('pear','Spearmint'),('pear','Pear Trees'),('cucumber','Seed (Cucumber)'),('blackberry','Blackberry Jam')]:
            row=dict(crop_labels=term,product_service_labels=term,ambiguous_labels='')
            self.assertEqual(roles(row,commodity),[])
        self.assertEqual(related_labels(dict(crop_labels='Spearmint',product_service_labels='',ambiguous_labels=''),'pear'),[])
        self.assertTrue(related_labels(dict(crop_labels='Blackberries',product_service_labels='',ambiguous_labels=''),'blackberry'))
    def test_cold_chain_coverage_and_outgoing_counts(self):
        bundle=json.loads((Path(__file__).resolve().parents[1]/'visualizations'/'graphs.json').read_text())
        from collections import Counter
        expected={'blackberry':(46,30,27),'grapefruit':(29,19,13),'pear':(55,43,16),
                  'celery':(62,36,38),'cucumber':(61,44,21),'asparagus':(24,9,18)}
        for commodity,(total,growers,products) in expected.items():
            graph=bundle['graphs'][commodity]
            self.assertEqual((len(graph['nodes']),graph['summary']['stage_counts']['crop'],graph['summary']['stage_counts']['general_product']),(total,growers,products))
            outgoing=Counter(e['source'] for e in graph['edges'])
            for source in graph['nodes']:
                targets=[n for n in graph['nodes'] if 'general_product' in n['roles'] and n['latitude'] is not None and n['id']!=source['id']]
                count=min(bundle['k'],len(targets)) if 'crop' in source['roles'] and source['latitude'] is not None else 0
                self.assertEqual(outgoing[source['id']],count)
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
