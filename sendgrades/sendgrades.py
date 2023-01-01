# grade sender: takes CSV (with four data per row: name, email, grade, comment) and sends a batch email
#   created by Pedro Lopes (2019)
#   with contributions by Shan-Yuan Teng (2020)


# CSV and args
import csv
import argparse

# Google GMAIL API
from Google import Create_Service
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# configure your sender email 
sender_email = ""

parser = argparse.ArgumentParser(description='send assignment emails to students')
parser.add_argument('grades_file', help='csv file with four data per row: name, email, grade, comment')
parser.add_argument('--preview', action='store_true', help='preview csv parsing')
parser.add_argument('--debug', action='store_true', help='only send to us')
args = parser.parse_args()

preview_flag = args.preview
debug_flag = args.debug
grades_file = args.grades_file

print('\033[1m', end='')
if debug_flag:
    print("[debug mode] only send to us")
if preview_flag:
    print("[preview mode] only parse csv")
if not debug_flag and not preview_flag:
    print("[real-deal mode] you are about to send a bunch of emails")
    ans = input("Confirm you have updated the email message accordingly (Y/N)")
    if ans != "Y":
        sys.exit(0)
print('\033[0m', end='');

# instatiate the google service (see Google API's documentation on how to create a 'credentials.json' file)
CLIENT_SECRET_FILE = 'credentials.json'
API_NAME = 'gmail'
API_VERSION = 'v1'
SCOPES = ['https://mail.google.com/']
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

# start reading the CSV file (respect the format using four data per row: name, email, grade, comment) 
# note: you can skip sending a grade by marking a person's name as "scriptSkip" in the CSV data
with open(grades_file) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    skip_count = 0
    for row in csv_reader:
        if row[1].find("@") != -1:
            if row[0] == "scriptSkip":
               print(f'skipping this row, regarding: {row[1]}')
               skip_count +=1
               continue
            print(f'{row[0]} (email: {row[1]}) had: {row[2]}\n Comments: {row[4]} ')
            print()
            line_count += 1
            mimeMessage = MIMEMultipart()
            if debug_flag:
                mimeMessage['to'] = 'insert-email-here-of-who-gets-the-debug-messages' #only-needed-for-debug
                mimeMessage['cc'] = 'insert-email-here-of-who-gets-the-debug-messages' #only-needed-for-debug
            else:
                mimeMessage['to'] = f"{row[1]}"
                mimeMessage['cc'] = 'insert-any-email-that-will-be-on-cc'
            filename=f"{row[4]}"                
            mimeMessage['subject'] = "Grades" #adjust this subject line as you wish
            emailMsg = f"""
Hey {row[0]}, 

Comments: {row[4]}

Grade: {row[2]} 

"""
# you can adjust this text as you wish, e.g., add more text, flip things around, add signatures, etc.
          
            mimeMessage.attach(MIMEText(emailMsg, 'plain'))
            raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()
            print(emailMsg)
            print("---------------")
            if not preview_flag:
                 message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()
                
    print(f'Done. Processed {line_count} grades via email. Check output for details.')
    print("skipped: ",end = '')
    print(skip_count)
