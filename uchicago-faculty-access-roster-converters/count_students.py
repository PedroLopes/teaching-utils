#!/usr/bin/env python3
"""Count unique students in a course-enrollment CSV by course level.

By default, 200-level courses are undergraduate and 300-level-or-higher
courses are graduate.  The course level is read from the Course column, so
the script works for entries such as "CMSC 20300", "MATH 30100", or "BIO 245".

Examples:
    python3 count_students.py 2026-10-01.csv
    python3 count_students.py enrollments.csv --course-column "Course Number"
    python3 count_students.py enrollments.csv --grad-min 400
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


def find_column(fieldnames: Iterable[str], requested: str | None, choices: tuple[str, ...]) -> str:
    """Return a requested column or a case-insensitive conventional match."""
    names = list(fieldnames)
    if requested:
        if requested not in names:
            raise ValueError(f'Column {requested!r} was not found. Available columns: {", ".join(names)}')
        return requested

    normalized = {name.strip().casefold(): name for name in names}
    for choice in choices:
        if choice.casefold() in normalized:
            return normalized[choice.casefold()]
    raise ValueError(
        f"Could not identify a column for {choices[0]!r}. "
        f"Use the corresponding --*-column option. Available columns: {', '.join(names)}"
    )


def course_level(course: str) -> int | None:
    """Return a catalog level (e.g., 200) from a course label, if recognizable."""
    # Most catalogs encode the level in the first digit: 20300, 30100, 245, etc.
    # Prefer sequences with at least three digits so department codes never match.
    codes = re.findall(r"\d{3,}", course)
    if not codes:
        return None
    first_digit = codes[0].lstrip("0")[:1]
    return int(first_digit) * 100 if first_digit else None


def student_key(row: dict[str, str], id_column: str, name_columns: tuple[str | None, ...]) -> tuple[str, ...] | None:
    """Use ID when available; otherwise use a stable name fallback for deduplication."""
    student_id = (row.get(id_column) or "").strip()
    if student_id:
        return ("id", student_id)
    name = tuple((row.get(column) or "").strip().casefold() for column in name_columns if column)
    return ("name", *name) if any(name) else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Count unique students by enrolled course level.")
    parser.add_argument("csv_file", type=Path, help="Enrollment CSV to analyze")
    parser.add_argument("--course-column", help="Name of the course-number column (default: auto-detect)")
    parser.add_argument("--id-column", help="Name of the student-ID column (default: auto-detect)")
    parser.add_argument(
        "--grad-min",
        type=int,
        default=300,
        help="Lowest course level considered graduate (default: 300)",
    )
    args = parser.parse_args()

    with args.csv_file.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise SystemExit("The CSV has no header row.")

        try:
            course_column = find_column(reader.fieldnames, args.course_column, ("Course", "Course Number", "CourseName"))
            id_column = find_column(reader.fieldnames, args.id_column, ("ID", "Student ID", "StudentID", "Student Id"))
        except ValueError as error:
            raise SystemExit(str(error)) from error

        normalized = {name.strip().casefold(): name for name in reader.fieldnames}
        name_columns = tuple(normalized.get(name) for name in ("lastname", "firstname", "middlename", "name"))

        # A student taking more than one listed course is counted once. Graduate
        # takes precedence, avoiding a student appearing in both final categories.
        student_levels: dict[tuple[str, ...], set[int]] = defaultdict(set)
        enrollment_rows = 0
        skipped_rows = 0
        for row in reader:
            if not any((value or "").strip() for value in row.values()):
                continue
            key = student_key(row, id_column, name_columns)
            level = course_level((row.get(course_column) or "").strip())
            if key is None or level is None:
                skipped_rows += 1
                continue
            enrollment_rows += 1
            student_levels[key].add(level)

    categories = Counter()
    level_counts = Counter()
    for levels in student_levels.values():
        for level in levels:
            level_counts[level] += 1
        if any(level >= args.grad_min for level in levels):
            categories["Graduate"] += 1
        elif any(200 <= level < args.grad_min for level in levels):
            categories["Undergraduate"] += 1
        else:
            categories["Other / unclassified"] += 1

    print(f"Unique students: {len(student_levels)}")
    print(f"Undergraduate (200-level): {categories['Undergraduate']}")
    print(f"Graduate ({args.grad_min}-level and above): {categories['Graduate']}")
    print(f"Other / unclassified: {categories['Other / unclassified']}")
    print(f"Enrollment rows analyzed: {enrollment_rows}")
    if level_counts:
        print("Course-level breakdown: " + ", ".join(f"{level}-level: {count}" for level, count in sorted(level_counts.items())))
    if skipped_rows:
        print(f"Rows skipped (missing student ID/name or recognizable course number): {skipped_rows}")


if __name__ == "__main__":
    main()
