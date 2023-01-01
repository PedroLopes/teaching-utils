# CSV and args
import csv
import argparse
import sys

parser = argparse.ArgumentParser(description='Takes a .csv file from Faculty Access and converts into a text output that is ready for bulk import at the UChicago Lists email server')
parser.add_argument('roster_file', help='csv file from faculty access, do not edit or swap collumns around')
parser.add_argument('--debug', action='store_true', help='show verbose debug while running')
args = parser.parse_args()

debug = args.debug
roster = args.roster_file

with open(roster) as csvfile:
    reader = csv.DictReader(csvfile)
    count  = 0
    print("---------------------------------")
    for row in reader:
        count += 1
        if debug:
            print("\tNew row (email):\t" + row['Email'])
            print("\tFirstName:\t\t" + row['FirstName'])
            print("\tPreferredName:\t\t" + row['PreferredName'])
            print("\tLastName:\t\t" + row['LastName'])
        username = ""
        if row['PreferredName'] != "":
            username = row['PreferredName'].replace(" ", "") + row['LastName'].replace(" ", "")
        else:
            username = row['FirstName'].replace(" ", "") + row['LastName'].replace(" ", "")
        print(row['Email'] + " " + username)
    print("---------------------------------")
    print("Done, processed " + str(count) + " entries from " + str(roster))  
