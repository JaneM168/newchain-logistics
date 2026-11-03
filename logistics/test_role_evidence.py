import unittest
from role_evidence import FIELDS, classify
from commodity_graph import caff_nodes


def entry(**changes):
    row=dict.fromkeys(FIELDS, '')
    row.update(business_id='example',name='Example Farm',listing_url='https://caff.org/directory/example/',
               address='123 Test St, Fresno, FRESNO, California 93722, US', state='California',zip='93722',
               commodity='pear', listed_label='Pears')
    row.update(changes)
    return row


def reviewed(**changes):
    return entry(asserted_role='grower',evidence_type='published_statement',
                 evidence_text='We grow pears on our farm.', evidence_url='https://example.org/crops',
                 checked_on='2026-11-03',review_status='accepted',**changes)


class RoleEvidenceTests(unittest.TestCase):
    def test_label_is_unknown_even_if_called_farm(self):
        result=classify([entry()])[0]
        self.assertEqual(result['roles'],[])
        self.assertEqual(result['role_status'],'commodity_listed_role_unknown')
        nodes,review=caff_nodes([result],'pear',{}, {})
        self.assertEqual(nodes,[])
        self.assertEqual(review[0]['reason'],'commodity_listed_role_unknown')
    def test_only_reviewed_evidence_supports_role(self):
        row=reviewed()
        self.assertEqual(classify([row])[0]['roles'],['grower'])
        for field,value in [('evidence_type','listing_label'),('evidence_url',''),('checked_on','bad'),('checked_on','2999-01-01'),('review_status','pending'),('evidence_text','')]:
            with self.subTest(field=field,value=value):
                self.assertEqual(classify([dict(row,**{field:value})])[0]['roles'],[])
    def test_roles_accumulate_and_seller_does_not_imply_grower(self):
        seller=dict(reviewed(),asserted_role='seller',evidence_text='We sell pears.')
        self.assertEqual(classify([seller])[0]['roles'],['seller'])
        result=classify([seller,reviewed()])[0]
        self.assertEqual(set(result['roles']),{'grower','seller'})
        index={('CA','fresno'):{1:dict(latitude=36.7,longitude=-119.8,geonameid=1)}}
        nodes,review=caff_nodes([result],'pear',index,{'california':'CA'})
        self.assertEqual(nodes[0]['roles'],['crop','general_product'])
        self.assertEqual(nodes[0]['id'],'caff:example')
        self.assertEqual(len(nodes[0]['role_evidence']),2)
        self.assertEqual(review,[])
    def test_metadata_conflicts_fail(self):
        with self.assertRaises(ValueError):
            classify([entry(),entry(address='different address')])

if __name__=='__main__':
    unittest.main()
