import os
from datetime import datetime


from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from PyFiles.Getters import get_nickname
from PyFiles.config import SERVICE_ACCOUNT_FILE, SCOPES, SPREADSHEET_ID


def get_google_sheets_service():
    """Authenticate and return a Google Sheets service object."""
    creds = None
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service
def add_sheet_row(amount: float, user_id, client_name: str, website: str, delivery_man, full_name, commission=0, account_type='', account_id=''):
    """Add a new row to the Google Sheet with a white background."""
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from datetime import datetime

    # Calculate the עמלה (commission fee) and assign account information based on account_type
    bank_transfer = ''
    bit = ''
    paybox = ''

    if account_type == 'B':  
        bit = account_id
        calculated_commission = commission * 0.01 * amount
        delivery_man = ''
    elif account_type == 'P':  
        paybox = account_id
        delivery_man = ''
        calculated_commission = commission * 0.01 * amount
    elif account_type == 'M':  
        bank_transfer = full_name
        delivery_man = ''
        calculated_commission = commission * 0.01 * amount
    else:  # Default case
        if delivery_man == '0':  # Check if delivery_man has a non-zero value
            delivery_man = 
            calculated_commission = 0
        else:
            calculated_commission = 25

    # Build the data for the new row
    log_entry = [
        datetime.now().isoformat(),  # תאריך הפקדה
        client_name,  # שם לקוח
        get_nickname(int(user_id)),  # סוכן
        bank_transfer,  
        bit,  
        paybox,  
        delivery_man,  # משיכה
        amount,  # סכום הפקדה
        website,  # אתר
        '',  # נקודות לפי
        calculated_commission,  # עמלה
    ]

    # Get the Google Sheets service
    service = get_google_sheets_service()

    # Add the row
    values = [log_entry]
    response = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='A2:L',
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": values}
    ).execute()

    # Get the updated row index
    updates = response.get("updates", {})
    updated_range = updates.get("updatedRange", "")
    row_start = updated_range.split("!")[1].split(":")[0]  # e.g., "A21"
    row_index = int(''.join(filter(str.isdigit, row_start)))  # Extract the number part, e.g., 21

    # Apply a white background to the added row
    try:
        requests = [
            {
                "updateCells": {
                    "rows": [
                        {
                            "values": [
                                {
                                    "userEnteredFormat": {
                                        "backgroundColor": {
                                            "red": 1.0,
                                            "green": 1.0,
                                            "blue": 1.0,
                                        }
                                    }
                                }
                                for _ in log_entry  # One formatting cell per column
                            ]
                        }
                    ],
                    "range": {
                        "sheetId": 0,  # Update with your actual sheet ID
                        "startRowIndex": row_index - 1,
                        "endRowIndex": row_index,
                        "startColumnIndex": 0,
                        "endColumnIndex": len(log_entry),
                    },
                    "fields": "userEnteredFormat.backgroundColor",
                }
            }
        ]
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": requests}
        ).execute()
        print("Log added with white background.")
    except HttpError as error:
        print(f"An error occurred: {error}")

