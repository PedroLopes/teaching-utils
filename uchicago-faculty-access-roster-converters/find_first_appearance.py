#!/usr/bin/env python3
"""Find the earliest dated CSV in which a student appears.

Examples:
    python3 find_first_appearance.py /path/to/rosters "jane@example.edu"
    python3 find_first_appearance.py /path/to/rosters "Jane Doe"
    python3 find_first_appearance.py /path/to/rosters --email jane@example.edu

CSV filenames must contain a date, such as 2026-01-15.csv, 01-15-2026.csv,
or 20260115.csv. Files are searched from oldest to newest by that date.

Created by Prof. Pedro Lopes in 2026 as part of teaching tools.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date, datetime
from pathlib import Path


DATE_PATTERNS = (
    "%Y-%m-%d", "%Y_%m_%d", "%Y.%m.%d", "%Y%m%d",
    "%m-%d-%Y", "%m_%d_%Y", "%m.%d.%Y",
    "%m-%d-%y", "%m_%d_%y", "%m.%d.%y",
)


def date_from_filename(path: Path) -> date:
    """Extract a date from a CSV filename, accepting several common formats."""
    stem = path.stem
    candidates = re.findall(
        r"\d{4}[-_.]\d{1,2}[-_.]\d{1,2}|\d{8}|\d{1,2}[-_.]\d{1,2}[-_.]\d{2,4}",
        stem,
    )
    for candidate in candidates:
        for pattern in DATE_PATTERNS:
            try:
                return datetime.strptime(candidate, pattern).date()
            except ValueError:
                pass
    raise ValueError(
        f"Cannot read a date from '{path.name}'. Rename it to include a date "
        "such as 2026-01-15.csv."
    )


def normalized(value: str | None) -> str:
    return " ".join((value or "").casefold().split())


def matching_rows(path: Path, query: str, email: bool) -> list[dict[str, str]]:
    matches = []
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        required = {"LastName", "FirstName", "Email"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name} is missing required column(s): {', '.join(sorted(missing))}")

        for row in reader:
            if email:
                found = normalized(row.get("Email")) == query
            else:
                full_name = normalized(f"{row.get('FirstName', '')} {row.get('MiddleName', '')} {row.get('LastName', '')}")
                found = query == full_name or query == normalized(
                    f"{row.get('FirstName', '')} {row.get('LastName', '')}"
                )
            if found:
                matches.append(row)
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(description="Find the first dated CSV containing a person.")
    parser.add_argument("directory", type=Path, help="Directory containing dated CSV files")
    parser.add_argument("query", nargs="?", help="Person's email address or name (for example, 'Jane Doe')")
    parser.add_argument("--email", metavar="ADDRESS", help="Search by email address explicitly")
    args = parser.parse_args()

    if bool(args.query) == bool(args.email):
        parser.error("Provide exactly one search value: QUERY or --email ADDRESS.")
    if not args.directory.is_dir():
        parser.error(f"Not a directory: {args.directory}")

    search_by_email = args.email is not None or "@" in (args.query or "")
    query = normalized(args.email if args.email is not None else args.query)

    dated_files = []
    for path in args.directory.glob("*.csv"):
        try:
            dated_files.append((date_from_filename(path), path))
        except ValueError:
            # Files such as responses.csv are not dated roster snapshots.
            # Ignore them rather than stopping the search.
            continue
    dated_files.sort(key=lambda item: (item[0], item[1].name.casefold()))

    if not dated_files:
        print("No dated CSV files found.", file=sys.stderr)
        return 2

    for file_date, path in dated_files:
        try:
            matches = matching_rows(path, query, search_by_email)
        except (OSError, UnicodeDecodeError, ValueError) as error:
            print(f"Error reading {path.name}: {error}", file=sys.stderr)
            return 2
        if matches:
            print(path.name)
            return 0

    print("No matching person found.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
