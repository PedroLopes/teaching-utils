#!/usr/bin/env python3
"""Create enrollment and student-background plots from a roster CSV.

Examples:
    python3 visualize_roster.py fresh.csv
    python3 visualize_roster.py fresh.csv --output-dir plots
    python3 visualize_roster.py fresh.csv --include-dropped

The first four plots describe currently enrolled students (Dropped? = FALSE)
by default. The time plot treats the earliest date as a static baseline and
shows later additions in green and withdrawals in red.

Created by Prof. Pedro Lopes in 2026 as part of teaching tools.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt


plt.style.use("seaborn-v0_8-whitegrid")
COLOR = "#6b8e5a"
ACCENT = "#4c6b3d"
GRAY = "#6b7280"


def normalized_header(header: str) -> str:
    return re.sub(r"[ _?\-]", "", header.strip().lower())


def find_column(headers: list[str], name: str) -> str:
    matches = [header for header in headers if normalized_header(header) == name]
    if len(matches) != 1:
        raise ValueError(f"Roster must contain exactly one {name!r} column.")
    return matches[0]


def read_roster(path: Path) -> tuple[list[str], list[dict[str, str]], dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("Roster is missing a header row.")
        headers = list(reader.fieldnames)
        columns = {
            "dept": find_column(headers, "dept"),
            "year": find_column(headers, "yearofstudy"),
            "dropped": find_column(headers, "dropped"),
            "grad": find_column(headers, "grad"),
            "grad_type": find_column(headers, "gradtype"),
            "date_added": find_column(headers, "dateadded"),
            "date_dropped": find_column(headers, "datedropped"),
        }
        return headers, list(reader), columns


def is_true(value: str) -> bool:
    return value.strip().upper() == "TRUE"


def parse_undergraduate_year(value: str) -> int | None:
    match = re.match(r"\s*(\d+)", value or "")
    return int(match.group(1)) if match else None


def parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat((value or "").strip())
    except ValueError:
        return None


def save_figure(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def plot_majors(rows: list[dict[str, str]], dept_column: str, output_dir: Path) -> Counter[str]:
    counts = Counter(row.get(dept_column, "").strip() or "Unspecified" for row in rows)
    ordered = counts.most_common()
    labels = [item[0] for item in ordered][::-1]
    values = [item[1] for item in ordered][::-1]
    plt.figure(figsize=(10, max(4, 0.42 * len(labels) + 1)))
    plt.barh(labels, values, color=COLOR)
    plt.xlabel("Students")
    plt.title("Student majors")
    for index, value in enumerate(values):
        plt.text(value + 0.1, index, str(value), va="center", color=ACCENT)
    save_figure(output_dir / "major.png")

    with (output_dir / "major_counts.txt").open("w", encoding="utf-8") as handle:
        for major, count in ordered:
            handle.write(f"{major}: {count}\n")
    return counts


def plot_undergraduate_years(rows: list[dict[str, str]], columns: dict[str, str], output_dir: Path) -> tuple[float | None, float | None, int]:
    years = [
        year
        for row in rows
        if not is_true(row.get(columns["grad"], ""))
        for year in [parse_undergraduate_year(row.get(columns["year"], ""))]
        if year is not None
    ]
    if not years:
        return None, None, 0
    mean = sum(years) / len(years)
    sd = (sum((year - mean) ** 2 for year in years) / len(years)) ** 0.5
    plt.figure(figsize=(5, 5))
    plt.boxplot(years, patch_artist=True, boxprops={"facecolor": "#b7c9a8"}, medianprops={"color": ACCENT, "linewidth": 2})
    plt.scatter([1] * len(years), years, color=GRAY, alpha=0.65, zorder=3)
    plt.ylabel("Year of study")
    plt.xticks([1], ["Undergraduates"])
    plt.title("Undergraduate year of study")
    plt.text(1.18, mean, f"Mean = {mean:.2f}\nSD = {sd:.2f}\nn = {len(years)}", va="center", color=ACCENT)
    save_figure(output_dir / "undergraduate_year_boxplot.png")
    return mean, sd, len(years)


def plot_grad_counts(rows: list[dict[str, str]], grad_column: str, output_dir: Path) -> Counter[str]:
    counts = Counter("Graduate" if is_true(row.get(grad_column, "")) else "Undergraduate" for row in rows)
    labels = ["Undergraduate", "Graduate"]
    values = [counts[label] for label in labels]
    plt.figure(figsize=(6, 4.5))
    bars = plt.bar(labels, values, color=[GRAY, COLOR])
    plt.ylabel("Students")
    plt.title("Graduate and undergraduate students")
    for bar, value in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2, value + 0.2, str(value), ha="center", color=ACCENT)
    save_figure(output_dir / "graduate_undergraduate_counts.png")
    return counts


def plot_grad_types(rows: list[dict[str, str]], columns: dict[str, str], output_dir: Path) -> Counter[str]:
    counts = Counter(
        row.get(columns["grad_type"], "").strip() or "Unspecified"
        for row in rows
        if is_true(row.get(columns["grad"], ""))
    )
    ordered = counts.most_common()
    labels = [item[0] for item in ordered]
    values = [item[1] for item in ordered]
    plt.figure(figsize=(max(6, 1.4 * len(labels)), 4.5))
    bars = plt.bar(labels, values, color=COLOR)
    plt.ylabel("Students")
    plt.title("Graduate student types")
    plt.xticks(rotation=20, ha="right")
    for bar, value in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2, value + 0.1, str(value), ha="center", color=ACCENT)
    save_figure(output_dir / "graduate_types.png")
    return counts


def plot_students_added_deleted_after_baseline(
    rows: list[dict[str, str]], columns: dict[str, str], output_dir: Path
) -> tuple[int, int, int, int, int]:
    additions: defaultdict[date, int] = defaultdict(int)
    deletions: defaultdict[date, int] = defaultdict(int)
    dated_records = 0
    skipped_records = 0
    for row in rows:
        added = parse_iso_date(row.get(columns["date_added"], ""))
        if added is None:
            skipped_records += 1
            continue
        dated_records += 1
        additions[added] += 1
        dropped = parse_iso_date(row.get(columns["date_dropped"], ""))
        if dropped is not None:
            deletions[dropped] += 1

    event_dates = sorted(set(additions) | set(deletions))
    if not event_dates:
        raise ValueError("No valid ISO dates found in date_added.")
    baseline_date = event_dates[0]
    baseline_count = additions[baseline_date] - deletions[baseline_date]
    later_dates = [event_date for event_date in event_dates if event_date > baseline_date]
    later_additions = [additions[event_date] for event_date in later_dates]
    later_deletions = [deletions[event_date] for event_date in later_dates]

    plt.figure(figsize=(9, 4.8))
    if later_dates:
        plt.bar(later_dates, later_additions, width=0.35, color="#5b8c4b", label="Added")
        plt.bar(later_dates, [-count for count in later_deletions], width=0.35, color="#c84646", label="Deleted")
        plt.axhline(0, color=GRAY, linewidth=0.8)
        plt.legend(frameon=True)
    else:
        plt.text(0.5, 0.5, "No additions or deletions after the baseline date.", ha="center", va="center", transform=plt.gca().transAxes)
        plt.ylim(-1, 1)
    plt.ylabel("Students")
    plt.xlabel("Date")
    plt.title(f"Student changes after baseline ({baseline_count} students on {baseline_date.isoformat()})")
    if later_dates:
        plt.xticks(later_dates, [event_date.isoformat() for event_date in later_dates], rotation=25, ha="right")
    save_figure(output_dir / "students_added_deleted_after_baseline.png")
    return dated_records, skipped_records, baseline_count, sum(later_additions), sum(later_deletions)


def plot_students_over_time(rows: list[dict[str, str]], columns: dict[str, str], output_dir: Path) -> None:
    """Plot net enrollment over time, including same-day additions and withdrawals."""
    changes: defaultdict[date, int] = defaultdict(int)
    for row in rows:
        added = parse_iso_date(row.get(columns["date_added"], ""))
        if added is None:
            continue
        changes[added] += 1
        dropped = parse_iso_date(row.get(columns["date_dropped"], ""))
        if dropped is not None:
            changes[dropped] -= 1
    if not changes:
        raise ValueError("No valid ISO dates found in date_added.")

    dates = sorted(changes)
    totals: list[int] = []
    current = 0
    for event_date in dates:
        current += changes[event_date]
        totals.append(current)

    plt.figure(figsize=(9, 4.8))
    plt.step(dates, totals, where="post", color=ACCENT, linewidth=2.5)
    plt.scatter(dates, totals, color=COLOR, zorder=3)
    plt.ylabel("Registered students")
    plt.xlabel("Date")
    plt.title("Students over time (net enrollment)")
    plt.xticks(dates, [event_date.isoformat() for event_date in dates], rotation=25, ha="right")
    save_figure(output_dir / "students_over_time.png")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roster", type=Path, help="Roster CSV containing the requested columns")
    parser.add_argument("--output-dir", type=Path, default=Path("plots"), help="Folder for PNG plots and text summaries")
    parser.add_argument("--include-dropped", action="store_true", help="Include dropped students in the first four current-roster plots")
    args = parser.parse_args()

    try:
        _, rows, columns = read_roster(args.roster)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        current_rows = rows if args.include_dropped else [
            row for row in rows if not is_true(row.get(columns["dropped"], ""))
        ]
        majors = plot_majors(current_rows, columns["dept"], args.output_dir)
        mean, sd, undergraduate_n = plot_undergraduate_years(current_rows, columns, args.output_dir)
        grad_counts = plot_grad_counts(current_rows, columns["grad"], args.output_dir)
        grad_types = plot_grad_types(current_rows, columns, args.output_dir)
        dated_records, skipped_records, baseline_count, later_added, later_deleted = plot_students_added_deleted_after_baseline(
            rows, columns, args.output_dir
        )
        plot_students_over_time(rows, columns, args.output_dir)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print("MAJORS (descending)")
    for major, count in majors.most_common():
        print(f"{major}: {count}")
    print(f"\nCURRENT STUDENTS: {len(current_rows)}")
    print(f"GRADUATE: {grad_counts['Graduate']}")
    print(f"UNDERGRADUATE: {grad_counts['Undergraduate']}")
    print("\nGRADUATE TYPES")
    for grad_type, count in grad_types.most_common():
        print(f"{grad_type}: {count}")
    if mean is None:
        print("\nUNDERGRADUATE YEAR: no numeric YearOfStudy values found.")
    else:
        print(f"\nUNDERGRADUATE YEAR: mean = {mean:.2f}, SD = {sd:.2f}, n = {undergraduate_n}")
    print(
        f"\nSTUDENT CHANGES AFTER BASELINE: {baseline_count} students on the first date; "
        f"{later_added} later added, {later_deleted} later deleted."
    )
    print(f"{dated_records} dated records, {skipped_records} skipped for blank/invalid date_added.")
    print(f"Plots written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
