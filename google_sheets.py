import os
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CALL_QUEUE_SHEET_ID = os.getenv("CALL_QUEUE_SHEET_ID")

def _get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS_PATH, scope)
    client = gspread.authorize(creds)
    return client

def log_response(phone_number, responses):
    client = _get_client()
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, phone_number] + responses
    sheet.append_row(row)
    print(f"📥 Logged to Google Sheet: {row}")

def get_call_queue():
    client = _get_client()
    sheet = client.open_by_key(CALL_QUEUE_SHEET_ID).sheet1
    data = sheet.get_all_values()
    header, rows = data[0], data[1:]

    queue = []
    for row in rows:
        if len(row) >= 2:
            phone, status = row[0], row[1].lower()
            if status not in ["done", "skip"]:
                queue.append(phone)
    return queue
