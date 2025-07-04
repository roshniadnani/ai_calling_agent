import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Replace with your actual sheet name
SHEET_NAME = "AI_Calling_Responses"
sheet = client.open(SHEET_NAME).sheet1

def log_response(caller_number, response_data):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, caller_number] + response_data
    sheet.append_row(row)