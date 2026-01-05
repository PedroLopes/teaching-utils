# CSV and args
import csv
import argparse
import sys

parser = argparse.ArgumentParser(description='Takes a .csv file from Faculty Access and converts into a .csv file that is ready for bulk import at dokuwiki. This will output a csv with the same name as input but with _wiki in filename')
parser.add_argument('roster_file', help='csv file from faculty access, do not edit or swap collumns around')
parser.add_argument('--debug', action='store_true', help='show verbose debug while running')
args = parser.parse_args()

debug = args.debug
roster = args.roster_file

# wiki format is
# The columns must contain, in order: 
# user-id, full name, email address and groups

output = open(str(roster[0:roster.find(".")]) + "_wiki.csv", "a")

with open(roster) as csvfile:
    reader = csv.DictReader(csvfile)
    count  = 0
    print("---------------------------------")
    for row in reader:
        count += 1
        username = ""
        fullname = ""
        if debug:
            print("\tNew row (email):\t" + row['Email'])
            print("\tFirstName:\t\t" + row['FirstName'])
            print("\tPreferredName:\t\t" + row['PreferredName'])
            print("\tLastName:\t\t" + row['LastName'])
        if row['PreferredName'] != "":
            username = row['PreferredName'].replace(" ", "") + row['LastName'].replace(" ", "")
            fullname = "\"" + row['PreferredName'] + " " + row['LastName'] + "\"" 
        else:
            username = row['FirstName'].replace(" ", "") + row['LastName'].replace(" ", "")
            fullname = "\"" + row['FirstName'] + " " + row['LastName'] + "\"" 
        print(username.lower().strip() + ", " + fullname.strip() + ", " + row['Email'].strip() + ", " + "user")
        output.write(username.lower().strip() + "," + fullname.strip() + "," + row['Email'].strip() + "," + "\"user\"")
        output.write("\n")
    print("---------------------------------")
    print("Done, processed " + str(count) + " entries from " + str(roster))  

output.close()
