# Contributing to FreeScrape

Thanks for your interest in improving FreeScrape!

## Ground rules

1. **Honest capability boundaries.** FreeScrape is a free, local-first tool. It has
   no paid proxy network and no CAPTCHA-solving service, and it never will.
   Documentation and marketing must not promise capabilities that do not exist.
2. **Local-first, zero-cost core.** Core functionality must work without any
   paid API keys. LLM integration stays optional and pluggable.
3. **Pipe-friendly output.** `--json` output must remain valid JSON on stdout
   (warnings go to stderr). If you touch output code, test on Windows pipes too.

## How to contribute

1. Fork the repo and create a branch: `git checkout -b feat/my-feature`
2. Install for development: `pip install -e .`
3. Make your change. Add or update tests under `tests/`.
4. Run the test suite: `python -m unittest discover -s tests -v`
5. Commit with a clear message and open a Pull Request against `main`.

## Adding a pipeline template

Pipelines are plain JSON files under `freescrape/pipelines/templates/`
(built-in) or `~/.freescrape/pipelines/` (user-defined). Each file needs:

```json
{
  "name": "my_pipeline",
  "description": "What it extracts",
  "url": "https://example.com",
  "item_selector": "css selector for repeating rows",
  "fields": [
    {"name": "title", "selector": "a", "attr": "text"}
  ]
}
```

## Reporting bugs

Open an issue with: the command you ran, the full output, your OS and Python
version, and whether the target site blocks plain HTTP requests. Note that
strongly anti-scraping sites may fail by design — FreeScrape does not bypass
CAPTCHAs or use residential proxies.
