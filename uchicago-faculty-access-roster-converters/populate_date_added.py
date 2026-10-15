#!/usr/bin/env python3
"""Fill a roster's date_added field from dated historical roster snapshots.

For every blank date_added field, this script calls find_first_appearance.py
with that student's email address.  The finder returns the filename of the
earliest snapshot containing that student; its embedded date becomes the
student's date_added value.

Examples:
    python3 populate_date_added.py roster.csv ../2026
    python3 populate_date_added.py roster.csv ../2026 roster_with_dates.csv
    python3 populate_date_added.py roster.csv ../2026 --finder /path/to/find_first_appearance.py

Created by Prof. Pedro Lopes in 2026 as part of teaching tools.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


DATE_PATTERNS = (
    "%Y-%m-%d", "%Y_%m_%d", "%Y.%m.%d", "%Y%m%d",
    "%m-%d-%Y", "%m_%d_%Y", "%m.%d.%Y",
    "%m-%d-%y", "%m_%d_%y", "%m.%d.%y",
)


def normalized_header(header: str) -> str:
    return re.sub(r"[ _-]", "", header.strip().lower())


def column_name(headers: list[str], expected: str) -> str:
    matches = [header for header in headers if normalized_header(header) == expected]
    if len(matches) != 1:
        raise ValueError(f"Roster must have exactly one {expected!r} column.")
    return matches[0]


def date_from_filename(filename: str) -> str:
    """Read a date from a dated roster filename and return ISO YYYY-MM-DD."""
    stem = Path(filename).stem
    candidates = re.findall(
        r"\d{4}[-_.]\d{1,2}[-_.]\d{1,2}|\d{8}|\d{1,2}[-_.]\d{1,2}[-_.]\d{2,4}",
        stem,
    )
    for candidate in candidates:
        for pattern in DATE_PATTERNS:
            try:
                return datetime.strptime(candidate, pattern).date().isoformat()
            except ValueError:
                continue
    raise ValueError(f"No readable date in finder result: {filename!r}")


def first_appearance(
    finder: Path, history_directory: Path, email: str
) -> tuple[str | None, str | None]:
    """Return (date_added, problem). A missing student is not a fatal problem."""
    result = subprocess.run(
        [sys.executable, str(finder), str(history_directory), email],
        text=True,
        capture_output=True,
        check=False,
    )
    output = result.stdout.strip()
    if result.returncode == 0:
        try:
            return date_from_filename(output), None
        except ValueError as error:
            return None, str(error)
    if result.returncode == 1 and output == "No matching person found.":
        return None, "not found in dated snapshots"
    detail = result.stderr.strip() or output or f"finder exited {result.returncode}"
    return None, detail


def default_output_path(roster: Path) -> Path:
    return roster.with_name(f"{roster.stem}_with_dates{roster.suffix}")


def populate_dates(
    roster_path: Path, history_directory: Path, output_path: Path, finder: Path
) -> tuple[int, int, int, list[tuple[str, str]]]:
    with roster_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("Roster is missing a header row.")
        headers = list(reader.fieldnames)
        rows = list(reader)

    email_column = column_name(headers, "email")
    date_added_column = column_name(headers, "dateadded")
    if not history_directory.is_dir():
        raise ValueError(f"History directory does not exist: {history_directory}")
    if not finder.is_file():
        raise ValueError(f"Cannot find finder script: {finder}")

    filled = already_present = 0
    missing: list[tuple[str, str]] = []
    for row_number, row in enumerate(rows, start=2):
        if row.get(date_added_column, "").strip():
            already_present += 1
            continue
        email = row.get(email_column, "").strip()
        if not email:
            missing.append((f"row {row_number}", "blank email"))
            continue
        found_date, problem = first_appearance(finder, history_directory, email)
        if found_date:
            row[date_added_column] = found_date
            filled += 1
        else:
            missing.append((email, problem or "not found"))

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return filled, already_present, len(missing), missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roster", type=Path, help="Roster CSV with a blank date_added column")
    parser.add_argument("history_directory", type=Path, help="Folder containing dated roster CSV snapshots")
    parser.add_argument("output", type=Path, nargs="?", help="Output CSV (default: <roster>_with_dates.csv)")
    parser.add_argument(
        "--finder",
        type=Path,
        default=Path("find_first_appearance.py"),
        help="Path to find_first_appearance.py (default: same working directory)",
    )
    args = parser.parse_args()
    output = args.output or default_output_path(args.roster)

    try:
        filled, already_present, missing_count, missing = populate_dates(
            args.roster, args.history_directory, output, args.finder
        )
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(
        f"Wrote {output}: {filled} date_added values filled, "
        f"{already_present} already present, {missing_count} not found."
    )
    if missing:
        print("\nNO FIRST APPEARANCE FOUND (left date_added blank)")
        for email, problem in missing:
            print(f"- {email}: {problem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
