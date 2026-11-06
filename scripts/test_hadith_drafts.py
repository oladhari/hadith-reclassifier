"""Offline checks for money limits and source-grounding invariants."""
import copy
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

from analyse_hadith_batch import Budget, RESERVATION, validate, ground_report


class DraftSafetyTests(unittest.TestCase):
    def test_concurrent_reservations_cannot_exceed_ceiling(self):
        with tempfile.TemporaryDirectory() as directory:
            budget=Budget(Path(directory)/'budget.json',Decimal('.5'))
            def reserve(number):
                try:return budget.reserve(number)
                except RuntimeError:return None
            with ThreadPoolExecutor(max_workers=12) as pool:
                accepted=[value for value in pool.map(reserve,range(12)) if value is not None]
            self.assertEqual(len(accepted),4)
            budget.settle(accepted[0],Decimal('.01'),{'response_id':'test'})
            data=json.loads(budget.path.read_text())
            self.assertLessEqual(Decimal(data['spent_usd'])+Decimal(data['reserved_usd']),Decimal('.5'))
            # An ambiguous failure is charged at its full reservation.
            budget.settle(accepted[1],RESERVATION,{'error':'timeout'})
            with self.assertRaises(ValueError):Budget(budget.path,Decimal('5'))

    def report(self):
        return {'layers':[{'code':f'L{i:02}','status':'needs_evidence','analysis':'يلزم التحقق','quotes':[],'next_step':'مراجعة الأصل'} for i in range(1,23)]}

    def test_unmatched_quote_withholds_its_analysis(self):
        report=self.report();record={'text':'نص أصلي'}
        report['layers'][0].update(status='text_observation',analysis='استنتاج غير موثق',quotes=['مختلق'])
        removed=ground_report(report,record)
        self.assertEqual(len(removed),1)
        self.assertEqual(report['layers'][0]['status'],'needs_evidence')
        self.assertNotIn('استنتاج غير موثق',report['layers'][0]['analysis'])
        self.assertEqual(report['layers'][0]['quotes'],[])
        validate(report,record)

    def test_fake_quotes_and_false_quran_completion_are_rejected(self):
        report=self.report();record={'text':'نص أصلي'}
        validate(report,record)
        invalid=copy.deepcopy(report);invalid['layers'][0]['quotes']=['كلام مختلق']
        with self.assertRaises(ValueError):validate(invalid,record)
        invalid=copy.deepcopy(report);invalid['layers'][1].update(status='text_observation',quotes=['نص'])
        with self.assertRaises(ValueError):validate(invalid,record)
        invalid=copy.deepcopy(report);invalid['layers'][0]['status']='text_observation'
        with self.assertRaises(ValueError):validate(invalid,record)
        invalid=copy.deepcopy(report);invalid['layers'][0]['code']='L02'
        with self.assertRaises(ValueError):validate(invalid,record)


if __name__=='__main__':unittest.main()
