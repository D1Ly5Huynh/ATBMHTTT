import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from oracle import evaluate_one, parser_changed  # noqa: E402


class OracleTests(unittest.TestCase):
    def test_script_alert_executes(self):
        result = evaluate_one("<script>alert(1)</script>")
        self.assertTrue(result.executed)
        self.assertTrue(result.parser_changed)

    def test_div_is_pasini_true_but_not_xss(self):
        payload = "<div>hello</div>"
        self.assertTrue(parser_changed(payload))
        result = evaluate_one(payload)
        self.assertFalse(result.executed)

    def test_encoded_query_executes_after_decode(self):
        payload = "http://x.test/search.php?q=%3cscript%3ealert(1)%3c/script%3e"
        result = evaluate_one(payload)
        self.assertTrue(result.executed)

    def test_title_hook(self):
        result = evaluate_one("<script>document.title='XSS_ORACLE'</script>")
        self.assertTrue(result.executed)

    def test_img_onerror_executes(self):
        result = evaluate_one("<img src=x onerror=alert(1)>")
        self.assertTrue(result.executed)

    def test_javascript_href_executes(self):
        result = evaluate_one('<a href="javascript:alert(1)">x</a>')
        self.assertTrue(result.executed)


if __name__ == "__main__":
    unittest.main()
