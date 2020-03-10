from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient import errors as gmail_errors
import base64
from config import Config
import requests
import time
from bs4 import BeautifulSoup
import logging

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']


logger = logging.getLogger('nec-logger') #create logger
logger.setLevel(logging.INFO) #set logging level
fh = logging.FileHandler('output.log') #create file handler and set log file
fh.setLevel(logging.INFO) #set logging level
ch = logging.StreamHandler() #create streamhandler
ch.setLevel(logging.ERROR) #set higher logging level
formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s', datefmt='%d-%b-%y %I:%M:%S %p') #set format for logs
fh.setFormatter(formatter) #set filehandler and streamhandler to use created format
ch.setFormatter(formatter) #set filehandler and streamhandler to use created format
logger.addHandler(fh) #add filehandler to logger
logger.addHandler(ch) #add streamhandler to logger


logger.info('Bot started successfully!')

def send_telegram(subject, message): #send incidents message via configured Telegram bot
    try:
        token = Config.token
        chat_id = Config.chat_id
        query = 'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&parse_mode=html&text={message}'.format(token=token, chat_id=chat_id, message=message)
        requests.get(query)
        logger.info("{} sent successfully.".format(subject))
    except Exception as e:
        logger.error('Error sending telegram message: {}'.format(e))

def update_labels(message_id): #update labels to READ and move to incidents folder
    try:
        labels_modify = {"removeLabelIds": ['UNREAD', 'INBOX'],
                         "addLabelIds": ['Label_3762316312411336423'] #incidents label
                         }
        service.users().messages().modify(userId='me', id=message_id, body=labels_modify).execute()
    except gmail_errors.HttpError as e:
        logger.error('An error occurred while updating labels: {}'.format(e))
    except Exception as e:
        logger.error("Unexpected error occurred while updating labels: {}".format(e))


# Authenticate at start of script 1st run
"""Shows basic usage of the Gmail API.
    """
creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
logger.info('Gmail authenticated successfully!')
print('Gmail authenticated successfully!')
logger.info('Listening for emails..')

### End of authentication


# Main function
def main():
    try: #error catching for main function
        #declaration
        subject = 'NA'

        # get list of new emails which are sent from configured sender_email and unread in inbox
        results = service.users().messages().list(userId='me', labelIds=['INBOX','UNREAD'], q='from:{}'.format(Config.sender_email)).execute()  #get list of emails

        try: #if there are new emails matching the list
            new_email = results['messages']  #get new emails info (mostly for the id)
            for mails in new_email:
                incidents = []
                message_id = mails['id'] #get email id
                email_get = service.users().messages().get(userId='me', id=message_id).execute() #get details of email

                payload = email_get['payload'] #get email payload
                headers = payload['headers'] #get email payload.headers

                data = payload['parts'][1]['body']['data']  # get email body payload
                body = str(base64.urlsafe_b64decode(data), "utf-8")  # decode body payload into human readable form

                # extract body contents
                soup = BeautifulSoup(body, features="html.parser")
                find = soup.find_all('p', 'MsoNormal')
                for i in find:
                    incidents.append(i.get_text()) #as soup.find_all returns a list, we append into a new list while extracting the text
                incidents_details = "\n".join(incidents) #and we join them up for a clean string format

                # get subject & sender. We assume the subject will be used as incident number & assignee
                for item in headers:
                    if item['name'] == 'Subject':
                        subject = item['value']

                #sending of Telegram messages with ticket info
                msg = '<b>{}</b> \n{}'.format(subject, incidents_details)
                send_telegram(subject, msg)

                #mark email as read so that future program run will not read the emails again.
                update_labels(message_id)

        except: #if no new emails which match search criteria, do nothing
            pass

    except Exception as error: #if error occur on main function
        logger.error('An error occurred while running main function: {}'.format(error))


while True:
    main()
    time.sleep(Config.sleep_time)

# if __name__ == '__main__':
#     main()

