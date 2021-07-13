import base64
import csv
from datetime import datetime
from email.mime.text import MIMEText
import math
import os
import random
import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

ENV_FROM_ADDR = 'FROM_ADDR'
SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        ]
timestamp_fmt = "%Y-%m-%d %H:%M:%S.%f"

log_file = "send_log.csv"
creds_file = "credentials.json"
token_file = "token.json"

def send_message(gmail, from_addr, to, subject, body):
        message = generate_message(from_addr, to, subject, body)
        try:
            start = datetime.utcnow()
            sent_message = (gmail.users().messages().send(userId='me', body=message).execute())
            send_time = datetime.utcnow() - start
            message_id = sent_message['id']
            print(f'Message {message_id} sent in {send_time}')
            return 200
        except HttpError as err:
            print(f'Error: {err}')
            return err.resp.status

def generate_message(from_addr, to_addr, subject, body):
    message = MIMEText(body)
    message['to'] = to_addr
    message['from'] = from_addr
    message['subject'] = subject

    str_message = message.as_string()
    encoded = base64.urlsafe_b64encode(str_message.encode("utf-8"))
    return {'raw': encoded.decode("utf-8")}

def log_result(pid, trial, time, status, address, subject, body):
    fmt_time = time.strftime(timestamp_fmt)
    with open(log_file, 'a') as csvfile:
        logwriter = csv.writer(csvfile)
        logwriter.writerow([pid, trial, fmt_time, status, address, subject, body])

def get_last_trial():
    last_trial = 0
    if os.path.exists(log_file):
        with open(log_file, 'r') as csvfile:
            logreader = csv.reader(csvfile)
            for row in logreader:
                trial = int(row[1])
                if trial > last_trial:
                    last_trial = trial
    return last_trial

def load_google_creds():
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
    with open(token_file, 'w') as token:
        token.write(creds.to_json())
    return creds

def build_gmail_client():
    creds = load_google_creds()
    service = build('gmail', 'v1', credentials=creds)
    return service

def main():
    from_addr = os.environ.get(ENV_FROM_ADDR)
    if not from_addr:
        raise Exception(f'Missing required environment variable: {ENV_FROM_ADDR}')

    gmail = None
    last_gmail_refresh = None

    pid = os.getpid()
    n = get_last_trial() + 1
    retries = 0
    while True:
        if not gmail or (datetime.utcnow() - last_gmail_refresh).total_seconds() > 600:
            if gmail:
                gmail.close()
            gmail = build_gmail_client()
            last_gmail_refresh = datetime.utcnow()

        trial = n
        n += 1
        now = datetime.utcnow()
        email = f'test{trial}@example.com'
        subject = f'Test email {trial}'
        body = f'This is test email #{trial}'

        status = send_message(gmail, from_addr, email, subject, body)
        log_result(pid, trial, now, status, email, subject, body)
        if status == 200:
            retries = 0
            print(f'{trial}: Message sent successfully')
        else:
            retries += 1
            sleep_time = round(0.2 * 1.5 ** retries, 3) # 200ms * 1.5^retries
            sleep_time = min(sleep_time, 60) # Cap to 60 seconds
            print(f'{trial}: Message send failed. Sleeping for {sleep_time} seconds...')
            time.sleep(sleep_time)

    print("Done")

main()
