"""Output helpers: human/JSON formatting, file writing, pipe-friendliness."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from rich.console import Console
from rich.table import Table

console = Console()


def out(
    data: Any,
    *,
    as_json: bool = False,
    pretty: bool = False,
    output_path: Optional[str] = None,
    humanizer: Optional[Callable[[Any], str]] = None,
) -> None:
    """Emit ``data`` to stdout (or a file) according to flags.

    - as_json / pretty -> JSON (compact or indented)
    - otherwise -> humanizer(data) text, falling back to JSON pretty
    - output_path -> also/only write to that file (extension decides format)
    """
    if output_path:
        _write_file(output_path, data, as_json, pretty, humanizer)
        # When writing to a file we still print a short confirmation to stderr
        # so stdout stays clean for piping.
        sys.stderr.write(f"written to {output_path}\n")
        return

    if as_json or pretty:
        text = json.dumps(data, ensure_ascii=False, indent=2 if pretty else None)
        console.print(text)
        return

    if humanizer is not None:
        console.print(humanizer(data))
    else:
        console.print(json.dumps(data, ensure_ascii=False, indent=2))


def _write_file(path: str, data: Any, as_json: bool, pretty: bool, humanizer) -> None:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in (".json",) or as_json:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2 if (pretty or suffix == ".json") else None), encoding="utf-8")
    elif suffix in (".md", ".markdown"):
        if humanizer is not None:
            p.write_text(humanizer(data), encoding="utf-8")
        else:
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    elif suffix in (".csv",):
        p.write_text(_to_csv(data), encoding="utf-8")
    else:
        # default: human text if available, else json
        content = humanizer(data) if humanizer else json.dumps(data, ensure_ascii=False, indent=2)
        p.write_text(content, encoding="utf-8")


def _to_csv(data: Any) -> str:
    """Best-effort CSV for a list of dicts."""
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        return json.dumps(data, ensure_ascii=False, indent=2)
    import csv
    import io

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(data[0].keys()))
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    return buf.getvalue()


def human_table(rows: list, columns: Dict[str, str], title: str = "") -> str:
    """Render a list of dicts as a Rich table string (used by humanizers)."""
    table = Table(title=title or None, show_lines=False)
    for key, header in columns.items():
        table.add_column(header)
    for row in rows:
        table.add_row(*[str(row.get(k, "")) for k in columns])
    console.print(table)
    return ""


def fatal(msg: str, code: int = 1) -> None:
    """Print an error to stderr and exit."""
    console.print(f"[red]error:[/red] {msg}", file=sys.stderr)
    raise SystemExit(code)
