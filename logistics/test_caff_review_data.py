"""Regression checks for provenance and ambiguous CAFF role decisions."""
import csv
import json
import unittest
from pathlib import Path
from role_evidence import read_evidence

ROOT=Path(__file__).resolve().parents[1]

class CAFFReviewDataTests(unittest.TestCase):
    def test_inventory_and_assessments_are_complete(self):
        root=ROOT/'data/caff_review'
        inventory=json.loads((root/'inventory.json').read_text())
        self.assertEqual(len(inventory),len({r['business_id'] for r in inventory}))
        self.assertEqual(len(inventory),412)
        assessed=json.loads((root/'assessments.json').read_text())
        expected={(r['business_id'],c) for r in inventory for c in r['matched_commodities']}
        self.assertEqual({(r['business_id'],r['commodity']) for r in assessed},expected)
        ledger=read_evidence(ROOT/'data/caff_role_evidence.csv')
        included={(r['business_id'],r['commodity']) for r in assessed if r['disposition']!='excluded_noncommodity_mention'}
        self.assertEqual({(r['business_id'],r['commodity']) for r in ledger},included)
    def test_quoted_evidence_matches_reviewed_snapshot(self):
        sources={str(r['id']):r for r in json.loads((ROOT/'data/caff_review/source_listings.json').read_text())}
        with (ROOT/'data/caff_role_evidence.csv').open(newline='') as f:
            rows=list(csv.DictReader(f))
        for row in rows:
            source=sources[row['business_id']]
            self.assertEqual(row['evidence_url'],source['url'])
            self.assertEqual(row['evidence_text'],'About Us: '+source['description']+'\nCrops & Products: '+source['products'])
            self.assertEqual(row['checked_on'],source['checked_on'])
    def test_mixed_sourcing_and_incidental_mentions(self):
        rows=read_evidence(ROOT/'data/caff_role_evidence.csv')
        by_key={(r['business_id'],r['commodity']):r for r in rows}
        self.assertNotIn(('14388','blackberry'),by_key) # sheep browse
        self.assertNotIn(('9016','blackberry'),by_key) # floral-source honey
        self.assertEqual(by_key['10261','coffee']['roles'],[]) # vegetable grower != coffee grower
        for key in [('9683','pear'),('39447','blackberry'),('10857','celery'),('10506','asparagus')]:
            self.assertNotIn('grower',by_key[key]['roles'])
        self.assertIn('grower',by_key['10588','pecan']['roles'])
        self.assertIn('grower',by_key['10071','coffee']['roles'])

if __name__=='__main__':
    unittest.main()
