import unittest
from factory2.core import Blocked
from factory2.review_packet import validate_complete


class SelfReviewTests(unittest.TestCase):
    def setUp(self):
        self.manifest={'factory_digest':'factory-v1','packets':[{'artifact_digest':'part-a'},{'artifact_digest':'part-b'}]}
        self.reviews=[{'artifact_digest':part,'verdict':'PASS','summary_es':'Resultado simulado de contrato','findings':[]}
                      for part in ('part-a','part-b')]

    def test_partial_duplicate_or_stale_review_blocks(self):
        for reviews in (self.reviews[:1],[self.reviews[0],self.reviews[0]],
                        [self.reviews[0],{**self.reviews[1],'artifact_digest':'old'}]):
            with self.assertRaises(Blocked): validate_complete(self.manifest,reviews)

    def test_blocked_part_blocks_whole(self):
        with self.assertRaises(Blocked): validate_complete(self.manifest,[self.reviews[0],{**self.reviews[1],'verdict':'BLOCK'}])

    def test_complete_parts_still_require_cross_component_review(self):
        result=validate_complete(self.manifest,self.reviews)
        self.assertEqual(result['status'],'NEEDS_CROSS_COMPONENT_REVIEW')
        self.assertFalse(result['publication_allowed'])


if __name__ == '__main__': unittest.main()
