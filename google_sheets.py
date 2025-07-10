import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import os
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()
logging.basicConfig(filename='logs/sheets_errors.log', level=logging.ERROR)

class GoogleSheetsService:
    def __init__(self):
        scope = ["https://spreadsheets.google.com/feeds", 
                "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH"), scope)
        self.client = gspread.authorize(creds)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def log_interaction(self, call_data: dict):
        try:
            sheet = self.client.open_by_key(os.getenv("GOOGLE_SHEET_ID")).sheet1
            sheet.append_row([
                call_data.get("timestamp"),
                call_data.get("phone_number"),
                call_data.get("question"),
                call_data.get("response"),
                call_data.get("status")
            ])
        except Exception as e:
            logging.error(f"Failed to log interaction: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def update_call_status(self, call_id: str, status: str):
        try:
            sheet = self.client.open_by_key(os.getenv("CALL_QUEUE_SHEET_ID")).sheet1
            records = sheet.get_all_records()
            
            for idx, row in enumerate(records, start=2):
                if row.get("call_id") == call_id:
                    sheet.update_cell(idx, 5, status)  # 5th column = status
                    break
        except Exception as e:
            logging.error(f"Failed to update call status: {str(e)}")
            raise