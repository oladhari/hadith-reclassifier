import unittest
from research_rijal import validate_candidate


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.page={'book_id':1,'page_id':2,'text':'راو آخر: كذاب.\nزيد: قال الناقد: صدوق.'}
        self.candidate={'narrator_name':'زيد','critic_name':'الناقد','exact_quote':'قال الناقد: صدوق.','entry_context':'زيد: قال الناقد: صدوق.','source_url':'https://shamela.ws/book/1/2','printed_locator':'1/5','identity_status':'not_matched','review_state':'unreviewed'}

    def test_verbatim_entry_is_only_draft_evidence(self):validate_candidate(self.candidate,self.page)

    def test_judgment_from_adjacent_narrator_is_rejected(self):
        self.candidate['exact_quote']='كذاب.'
        with self.assertRaises(ValueError):validate_candidate(self.candidate,self.page)

    def test_wrong_page_and_claimed_review_are_rejected(self):
        self.candidate['source_url']='https://shamela.ws/book/1/3'
        with self.assertRaises(ValueError):validate_candidate(self.candidate,self.page)
        self.candidate['source_url']='https://shamela.ws/book/1/2';self.candidate['review_state']='reviewed'
        with self.assertRaises(ValueError):validate_candidate(self.candidate,self.page)


if __name__=='__main__':unittest.main()
