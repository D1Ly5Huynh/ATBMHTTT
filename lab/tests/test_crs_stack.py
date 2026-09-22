import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from crs_client import APP, CRS_PL1, fetch, stack_up  # noqa: E402


class CrsStackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.health = stack_up()
        if not all(cls.health.values()):
            raise unittest.SkipTest(f"CRS stack down: {cls.health}")

    def test_app_reflects_script(self):
        hit = fetch(APP, "/html", "<script>alert(1)</script>")
        self.assertEqual(hit.status, 200)
        self.assertIn("<script>alert(1)</script>", hit.body)

    def test_pl1_blocks_raw_script(self):
        hit = fetch(CRS_PL1, "/html", "<script>alert(1)</script>")
        self.assertEqual(hit.status, 403)

    def test_pl1_allows_hello(self):
        hit = fetch(CRS_PL1, "/html", "hello")
        self.assertEqual(hit.status, 200)
