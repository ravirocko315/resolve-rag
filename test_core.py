"""Offline regression tests: no provider calls, credentials or paid requests."""
import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import core


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.sources = core.load_sources(Path(__file__).parent / "data" / "sources.json")

    def test_corpus_and_retrieval(self):
        self.assertEqual(len(self.sources), 3)
        hits = core.retrieve("How do I track a complaint?", self.sources)
        self.assertEqual(hits[0]["id"], "NCH-PROCESS")
        self.assertGreater(hits[0]["score"], 0)

    def test_no_match(self):
        self.assertEqual(core.retrieve("xyzzy", self.sources), [])
        self.assertEqual(core.retrieve("refund", self.sources, limit=0), [])
        self.assertEqual(core.retrieve("refund", []), [])

    def test_country_filter(self):
        foreign = {**self.sources[0], "country": "US"}
        self.assertEqual(core.retrieve("refund", [foreign]), [])

    def test_input_and_scope(self):
        for question in ("", "weather tomorrow", "python return statement", "income tax return"):
            with self.subTest(question=question):
                self.assertEqual(core.answer_question(question, self.sources)["sources"], [])
        result = core.answer_question("refund " * 400, self.sources)
        self.assertIn("shortened", result["warning"])

    def test_evidence_and_limits(self):
        result = core.answer_question("Am I guaranteed a refund?", self.sources)
        self.assertEqual(result["mode"], "evidence")
        self.assertIn("not quotations", result["answer"])
        self.assertIn("does not contain retailer-specific policies", result["answer"])
        self.assertIn("[NCH-", result["answer"])
        self.assertEqual(core.answer_question("refund", [])["sources"], [])

    def test_missing_ai_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            result = core.answer_question("refund", self.sources, use_ai=True)
        self.assertEqual(result["mode"], "evidence")
        self.assertIn("configuration is missing", result["warning"])

    def test_network_failure_falls_back(self):
        with patch.dict(os.environ, OPENAI_API_KEY="test-only", OPENAI_MODEL="test-only"):
            with patch("core._ai_answer", side_effect=TimeoutError):
                result = core.answer_question("refund", self.sources, use_ai=True)
        self.assertEqual(result["mode"], "evidence")
        self.assertIn("unavailable", result["warning"])
        self.assertNotIn("test-only", result["warning"])

    def api_response(self, text, finish="stop"):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "choices": [{"message": {"content": text}, "finish_reason": finish}]
        }).encode()
        opener = MagicMock()
        opener.open.return_value = response
        return patch("core.urllib.request.build_opener", return_value=opener)

    def test_valid_ai_citation(self):
        with self.api_response("General guidance [NCH-CONTACT]"):
            result = core._ai_answer("refund", self.sources, "test-only", "test-only")
        self.assertIn("[NCH-CONTACT]", result)

    def test_invalid_ai_responses(self):
        for text in ("No citations", "False [MADE-UP]", "Go https://evil.test [NCH-CONTACT]", "[NCH-CONTACT]]"):
            with self.subTest(text=text), self.api_response(text):
                with self.assertRaises(ValueError):
                    core._ai_answer("refund", self.sources, "test-only", "test-only")
        with self.api_response("Partial [NCH-CONTACT]", finish="length"):
            with self.assertRaises(ValueError):
                core._ai_answer("refund", self.sources, "test-only", "test-only")

    def test_bad_corpus(self):
        with patch.object(Path, "read_text", return_value="not JSON"):
            self.assertEqual(core.load_sources(Path("unused")), [])
        with patch.object(Path, "read_text", return_value=json.dumps([{}, self.sources[0], self.sources[0]])):
            self.assertEqual(len(core.load_sources(Path("unused"))), 1)

    def test_draft_has_placeholders(self):
        draft = core.complaint_draft("Example Shop", "Refund has not arrived")
        self.assertIn("Example Shop", draft)
        self.assertIn("Refund has not arrived", draft)
        self.assertIn("[Order/reference number]", draft)
        self.assertIn("Draft only", draft)


if __name__ == "__main__":
    unittest.main()
