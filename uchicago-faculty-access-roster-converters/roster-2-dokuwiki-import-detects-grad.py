# CSV and args
import csv
import argparse
import sys
import re
from pathlib import Path

""" 
This script takes the roster as per "Faculty Access" and generates a wiki ready csv to create users in a class wiki. It also detects who is signed up for a 300 level course, and marks them as "grad" users, on top of "user". 


Created by Prof. Pedro Lopes in 2026 as part of teaching tools.
"""

def course_level(course_label):
    """Return the catalog level encoded in a Faculty Access course label.

    For example, 20300 and 245 are 200-level courses, while 30100 is a
    300-level course.  This matches the course-level detection used by the
    roster-counting script.
    """
    match = re.search(r"\d{3,}", str(course_label or ""))
    if not match:
        return None

    first_nonzero_digit = next(
        (digit for digit in match.group() if digit != "0"), None
    )
    if first_nonzero_digit is None:
        return None

    return int(first_nonzero_digit) * 100


def wiki_groups(course_label):
    """Assign graduate students to both the user and grad DokuWiki groups."""
    level = course_level(course_label)
    return "user,grad" if level is not None and level >= 300 else "user"

parser = argparse.ArgumentParser(description='Takes a .csv file from Faculty Access and converts into a .csv file that is ready for bulk import at dokuwiki. This will output a csv with the same name as input but with _wiki in filename')
parser.add_argument('roster_file', help='csv file from faculty access, do not edit or swap collumns around')
parser.add_argument('--debug', action='store_true', help='show verbose debug while running')
args = parser.parse_args()

debug = args.debug
roster = args.roster_file

# wiki format is
# The columns must contain, in order: 
# user-id, full name, email address and groups

output_path = Path(roster).with_suffix("").with_name(
    Path(roster).stem + "_wiki.csv"
)

with open(roster, newline="") as csvfile, open(output_path, "w", newline="") as output:
    reader = csv.DictReader(csvfile)
    writer = csv.writer(output, lineterminator="\n")
    console_writer = csv.writer(sys.stdout, lineterminator="\n")
    count = 0
    print("---------------------------------")
    for row in reader:
        count += 1
        if debug:
            print("\tNew row (email):\t" + row['Email'])
            print("\tFirstName:\t\t" + row['FirstName'])
            print("\tLastName:\t\t" + row['LastName'])
            print("\tCourse:\t\t" + row.get('Course', ''))

        username = row['FirstName'].replace(" ", "") + row['LastName'].replace(" ", "")
        fullname = row['FirstName'].strip() + " " + row['LastName'].strip()
        groups = wiki_groups(row.get('Course', ''))
        record = [
            username.lower().strip(),
            fullname,
            row['Email'].strip(),
            groups,
        ]
        writer.writerow(record)
        console_writer.writerow(record)

    print("---------------------------------")
    print("Done, processed " + str(count) + " entries from " + str(roster))
