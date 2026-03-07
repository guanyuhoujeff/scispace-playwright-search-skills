#!/usr/bin/env python3
"""Build a SciSpace search URL with published_in_journal slugs from journal-slugs.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, List
from urllib.parse import quote


def default_journal_slug_paths() -> List[Path]:
    home = Path.home()
    cwd = Path.cwd()
    return [
        cwd / "journal-slugs.json",
        home / "journal-slugs.json",
        home / "Desktop" / "workspace" / "skills" / "scispace" / "journal-slugs.json",
    ]


def find_journal_slug_file(explicit_path: str | None) -> Path:
    if explicit_path:
        p = Path(explicit_path).expanduser()
        if p.exists():
            return p
        raise FileNotFoundError(f"journal-slugs file not found: {p}")

    for candidate in default_journal_slug_paths():
        if candidate.exists():
            return candidate

    candidates = "\n".join(f"- {p}" for p in default_journal_slug_paths())
    raise FileNotFoundError(
        "No journal-slugs.json found in default paths. Checked:\n" + candidates
    )


def iter_string_values(node: Any) -> Iterable[str]:
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from iter_string_values(value)
    elif isinstance(node, list):
        for value in node:
            yield from iter_string_values(value)


def collect_unique_slugs(payload: dict[str, Any]) -> List[str]:
    source_node: Any = payload.get("journals", payload)
    slugs: List[str] = []
    seen: set[str] = set()

    for raw in iter_string_values(source_node):
        slug = raw.strip()
        if not slug:
            continue
        if slug.lower() == "null":
            continue
        if slug in seen:
            continue
        seen.add(slug)
        slugs.append(slug)

    return slugs


def build_search_url(base_url: str, query: str, slugs: List[str]) -> str:
    if not slugs:
        raise ValueError("No valid journal slugs found.")
    encoded_query = quote(query, safe="")
    encoded_slugs = quote(",".join(slugs), safe="")
    return f"{base_url}?q={encoded_query}&published_in_journal={encoded_slugs}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a SciSpace search URL from journal-slugs.json"
    )
    parser.add_argument("--query", required=True, help="Search query text")
    parser.add_argument(
        "--journal-slugs-path",
        default=None,
        help="Optional explicit path to journal-slugs.json",
    )
    parser.add_argument(
        "--base-url",
        default="https://scispace.com/search",
        help="SciSpace search base URL",
    )
    parser.add_argument(
        "--write-url-file",
        default=None,
        help="Optional output path to save URL as plain text",
    )
    args = parser.parse_args()

    try:
        slug_path = find_journal_slug_file(args.journal_slugs_path)
        payload = json.loads(slug_path.read_text(encoding="utf-8"))
        slugs = collect_unique_slugs(payload)
        url = build_search_url(args.base_url, args.query, slugs)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.write_url_file:
        out_path = Path(args.write_url_file).expanduser()
        out_path.write_text(url + "\n", encoding="utf-8")

    summary = {
        "journal_slugs_path": str(slug_path.resolve()),
        "slug_count": len(slugs),
        "query": args.query,
        "url": url,
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
