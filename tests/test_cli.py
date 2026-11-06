"""Smoke tests for the FreeScrape CLI (no network required)."""
from click.testing import CliRunner

from freescrape.cli import cli


def test_help():
    r = CliRunner().invoke(cli, ["--help"])
    assert r.exit_code == 0
    assert "scrape" in r.output
    assert "search" in r.output


def test_version():
    r = CliRunner().invoke(cli, ["--version"])
    assert r.exit_code == 0
    assert "freescrape" in r.output


def test_budget():
    r = CliRunner().invoke(cli, ["budget", "--json"])
    assert r.exit_code == 0
    assert '"plan"' in r.output


def test_config_list():
    r = CliRunner().invoke(cli, ["config", "list"])
    assert r.exit_code == 0
    assert "user_agent" in r.output


def test_pipelines_search():
    r = CliRunner().invoke(cli, ["pipelines", "search", "--json"])
    assert r.exit_code == 0
    assert "hackernews" in r.output
