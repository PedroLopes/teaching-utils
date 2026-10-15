#!/usr/bin/env python3
"""Update a roster's dropped column from a newer roster.

The input roster is the master list: its row order and its existing values are
preserved. Students absent from the new roster are marked TRUE in the dropped
column; students still present are marked FALSE. Students present only in the
new roster are appended after every original input row and are marked FALSE.

Use --init with one roster to create an initialized master roster. It marks
every student as present, records today's date_added, and calculates Grad and
Grad-Type.

Created by Prof. Pedro Lopes in 2026 as part of teaching tools.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date
from pathlib import Path

MATCH_FIELDS = ("ID", "Email")
GRAD_PATTERN = re.compile(r"^[A-Za-z]+\s+3\d+")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path}: CSV is missing a header row.")
        return list(reader.fieldnames), list(reader)


def normalize_header(header: str) -> str:
    return re.sub(r"[ _-]", "", header.strip().lower().rstrip("?"))


def find_column(headers: list[str], normalized_name: str) -> str:
    matches = [
        header
        for header in headers
        if normalize_header(header) == normalized_name
    ]
    if len(matches) != 1:
        raise ValueError(f"Input roster must have exactly one {normalized_name!r} column.")
    return matches[0]


def find_tracking_columns(headers: list[str]) -> tuple[str, str, str, str, str]:
    dropped = find_column(headers, "dropped")
    grad = find_column(headers, "grad")
    grad_type = find_column(headers, "gradtype")
    date_added = find_column(headers, "dateadded")
    date_dropped = find_column(headers, "datedropped")
    return dropped, grad, grad_type, date_added, date_dropped


def graduate_status(row: dict[str, str]) -> tuple[str, str]:
    """Return values for Grad and Grad-Type according to the course/year rules."""
    course = row.get("Course", "").strip()
    if not GRAD_PATTERN.match(course):
        return "FALSE", ""

    year = row.get("YearOfStudy", "").strip().upper()
    if year.startswith("M"):
        return "TRUE", "master"
    if year.startswith("D"):
        return "TRUE", "phd"
    if not year or not year[0].isalpha():
        return "TRUE", "undergrad-taking-grad"
    return "TRUE", ""


def key(row: dict[str, str]) -> tuple[str, str]:
    """Return a stable student identifier, preferring the institutional ID.

    This also permits an email-only roster.  An unchanged student whose email
    was edited will therefore still match by ID.
    """
    student_id = row.get("ID", "").strip()
    email = row.get("Email", "").strip().casefold()
    if student_id:
        return "ID", student_id
    if email:
        return "Email", email
    if not student_id and not email:
        raise ValueError("Each student needs at least an ID or Email value.")
    raise AssertionError("unreachable")


def duplicate_keys(rows: list[dict[str, str]], source: str) -> None:
    seen: dict[tuple[str, str], int] = {}
    for number, row in enumerate(rows, start=2):
        student_key = key(row)
        if student_key in seen:
            raise ValueError(
                f"Duplicate student in {source}: rows {seen[student_key]} and {number} "
                f"have matching {student_key[0]}={student_key[1]!r}."
            )
        seen[student_key] = number


def print_change_table(title: str, rows: list[dict[str, str]], headers: list[str]) -> None:
    """Print a compact, dependency-free CSV-style table for changed students."""
    if not rows:
        return
    widths = {
        header: max(len(header), *(len(row.get(header, "")) for row in rows))
        for header in headers
    }
    separator = "  ".join("-" * widths[header] for header in headers)

    print(f"\n{title}")
    print("  ".join(header.ljust(widths[header]) for header in headers))
    print(separator)
    for row in rows:
        print("  ".join(row.get(header, "").ljust(widths[header]) for header in headers))


def update_roster(
    input_path: Path, new_path: Path, output_path: Path
) -> tuple[int, int, int, list[dict[str, str]], list[dict[str, str]], list[str]]:
    input_headers, input_rows = read_csv(input_path)
    new_headers, new_rows = read_csv(new_path)
    (
        dropped_column,
        grad_column,
        grad_type_column,
        date_added_column,
        date_dropped_column,
    ) = find_tracking_columns(input_headers)

    tracking_columns = {
        dropped_column,
        grad_column,
        grad_type_column,
        date_added_column,
        date_dropped_column,
    }
    roster_headers = [header for header in input_headers if header not in tracking_columns]
    missing_from_new = [field for field in roster_headers if field not in new_headers]
    if missing_from_new:
        raise ValueError(
            "New roster is missing input fields: " + ", ".join(missing_from_new)
        )
    for field in MATCH_FIELDS:
        if field not in input_headers or field not in new_headers:
            raise ValueError(f"Both rosters must contain a {field!r} column.")

    duplicate_keys(input_rows, str(input_path))
    duplicate_keys(new_rows, str(new_path))
    new_by_key = {key(row): row for row in new_rows}
    input_keys = {key(row) for row in input_rows}
    today = date.today().isoformat()

    output_rows: list[dict[str, str]] = []
    removed_rows: list[dict[str, str]] = []
    added_rows: list[dict[str, str]] = []
    kept = dropped = 0
    for row in input_rows:
        output_row = {header: row.get(header, "") for header in input_headers}
        output_row[grad_column], output_row[grad_type_column] = graduate_status(row)
        if key(row) in new_by_key:
            output_row[dropped_column] = "FALSE"
            output_row[date_dropped_column] = ""
            kept += 1
        else:
            output_row[dropped_column] = "TRUE"
            output_row[date_dropped_column] = row.get(date_dropped_column, "") or today
            dropped += 1
            removed_rows.append(output_row)
        output_rows.append(output_row)

    added = 0
    for row in new_rows:
        if key(row) not in input_keys:
            output_row = {header: row.get(header, "") for header in roster_headers}
            output_row[dropped_column] = "FALSE"
            output_row[grad_column], output_row[grad_type_column] = graduate_status(row)
            output_row[date_added_column] = today
            output_row[date_dropped_column] = ""
            output_rows.append(output_row)
            added_rows.append(output_row)
            added += 1

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=input_headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)
    display_headers = [header for header in input_headers if header != dropped_column]
    return kept, dropped, added, removed_rows, added_rows, display_headers


def initialized_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"initialized_{input_path.name}")


def initialize_roster(input_path: Path, output_path: Path) -> int:
    """Create a dated master roster from one roster file."""
    headers, rows = read_csv(input_path)
    (
        dropped_column,
        grad_column,
        grad_type_column,
        date_added_column,
        date_dropped_column,
    ) = find_tracking_columns(headers)
    for field in ("Course", "YearOfStudy", *MATCH_FIELDS):
        if field not in headers:
            raise ValueError(f"Roster must contain a {field!r} column.")
    duplicate_keys(rows, str(input_path))

    today = date.today().isoformat()
    for row in rows:
        row[dropped_column] = "FALSE"
        row[grad_column], row[grad_type_column] = graduate_status(row)
        row[date_added_column] = today
        row[date_dropped_column] = ""

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize one roster; default output is initialized_<input filename>.csv",
    )
    parser.add_argument(
        "rosters",
        type=Path,
        nargs="+",
        help="Normal mode: INPUT NEW OUTPUT. --init: INPUT [OUTPUT]",
    )
    args = parser.parse_args()

    try:
        if args.init:
            if len(args.rosters) not in (1, 2):
                raise ValueError("--init requires INPUT_ROSTER and optional OUTPUT_ROSTER.")
            input_path = args.rosters[0]
            output_path = args.rosters[1] if len(args.rosters) == 2 else initialized_output_path(input_path)
            count = initialize_roster(input_path, output_path)
            print(f"Initialized {output_path}: {count} students dated {date.today().isoformat()}.")
            return 0
        if len(args.rosters) != 3:
            raise ValueError("Normal mode requires INPUT_ROSTER NEW_ROSTER OUTPUT_ROSTER.")
        kept, dropped, added, removed_rows, added_rows, display_headers = update_roster(
            args.rosters[0], args.rosters[1], args.rosters[2]
        )
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {args.rosters[2]}: {kept} retained, {dropped} dropped, {added} added.")
    print_change_table("REMOVED (marked as dropped)", removed_rows, display_headers)
    print_change_table("ADDED (appended to end)", added_rows, display_headers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
