"""Exercise Streamlit forms without starting a public server."""
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class AppTests(unittest.TestCase):
    def test_question_and_draft(self):
        app = AppTest.from_file(str(Path(__file__).parent / "app.py")).run()
        self.assertFalse(app.exception)
        app.text_area[0].input("How can I register a refund complaint?")
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertIn("[NCH-", app.session_state["guidance"]["answer"])
        self.assertEqual(app.session_state["guidance"]["mode"], "evidence")
        app.text_input[0].input("Example Shop")
        app.text_area[1].input("Refund has not arrived")
        app.button[1].click().run()
        self.assertFalse(app.exception)
        self.assertIn("Example Shop", app.session_state["editable_draft"])
        self.assertIn("Draft only", app.session_state["editable_draft"])


if __name__ == "__main__":
    unittest.main()
