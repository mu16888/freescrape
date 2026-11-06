"""Smoke tests for the FreeScrape CLI (no network required).

Written with unittest so CI can run them with zero extra dependencies:

    python -m unittest discover -s tests -v
"""
import json
import unittest

from click.testing import CliRunner

from freescrape.cli import cli


class CliSmokeTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_help(self):
        r = self.runner.invoke(cli, ["--help"])
        self.assertEqual(r.exit_code, 0, r.output)
        self.assertIn("scrape", r.output)
        self.assertIn("search", r.output)

    def test_version(self):
        r = self.runner.invoke(cli, ["--version"])
        self.assertEqual(r.exit_code, 0, r.output)
        self.assertIn("freescrape", r.output)

    def test_budget(self):
        r = self.runner.invoke(cli, ["budget", "--json"])
        self.assertEqual(r.exit_code, 0, r.output)
        self.assertIn('"plan"', r.output)

    def test_budget_json_is_parseable(self):
        """Regression: JSON output must stay valid through Windows pipes."""
        r = self.runner.invoke(cli, ["budget", "--json"])
        self.assertEqual(r.exit_code, 0, r.output)
        data = json.loads(r.output)
        self.assertIsInstance(data, dict)
        self.assertIn("plan", data)

    def test_config_list(self):
        r = self.runner.invoke(cli, ["config", "list"])
        self.assertEqual(r.exit_code, 0, r.output)
        self.assertIn("user_agent", r.output)

    def test_pipelines_search(self):
        r = self.runner.invoke(cli, ["pipelines", "search", "--json"])
        self.assertEqual(r.exit_code, 0, r.output)
        self.assertIn("hackernews", r.output)


if __name__ == "__main__":
    unittest.main()
