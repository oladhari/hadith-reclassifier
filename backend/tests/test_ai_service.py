import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.ai_service import AIService


class AIServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = AIService()
        self.service._client = Mock()
        self.result = dict(verdict='accepted', overall_score=75, chain_score=75,
                           content_score=75, ai_reasoning='Synthetic sample',
                           rejection_reasons=[])

    def response(self, text, status='completed'):
        self.service.client.responses.create.return_value = SimpleNamespace(
            output_text=text, status=status)

    def classify(self):
        return self.service.classify_hadith('Synthetic sample text', '', 'sample', 0)

    def test_json_and_fenced_json(self):
        for text in [json.dumps(self.result), '```json\n'+json.dumps(self.result)+'\n```']:
            self.response(text)
            self.assertEqual(self.classify(), self.result)
        args = self.service.client.responses.create.call_args.kwargs
        self.assertFalse(args['store'])
        self.assertEqual(args['text']['format']['type'], 'json_object')

    def test_invalid_json_and_contract(self):
        for text in ['{', '[]', '{}', json.dumps(dict(self.result, overall_score=101)),
                     json.dumps(dict(self.result, verdict='unknown'))]:
            self.response(text)
            with self.assertRaises(ValueError):
                self.classify()

    def test_incomplete_and_empty_are_rejected(self):
        for text, status in [(json.dumps(self.result), 'incomplete'), ('', 'completed'),
                             ('partial', 'failed'), ('partial', 'in_progress')]:
            self.response(text, status)
            with self.assertRaises(RuntimeError):
                self.classify()
            with self.assertRaises(RuntimeError):
                self.service.generate_book_entry('Synthetic sample', self.result)

    def test_book_entry_branches(self):
        for verdict, phrase in [('accepted', 'accepted hadith'), ('rejected', 'rejection entry')]:
            self.response('Sample entry')
            result = dict(self.result, verdict=verdict)
            self.assertEqual(self.service.generate_book_entry('Synthetic sample', result), 'Sample entry')
            args = self.service.client.responses.create.call_args.kwargs
            self.assertIn(phrase, args['input'][0]['content'])
            self.assertFalse(args['store'])

    def test_missing_key_fails_only_on_generation(self):
        service = AIService()
        with patch('app.services.ai_service.settings') as settings:
            settings.OPENAI_API_KEY.get_secret_value.return_value = ''
            with self.assertRaisesRegex(RuntimeError, 'OPENAI_API_KEY'):
                service.classify_hadith('sample', '', 'sample', 0)
