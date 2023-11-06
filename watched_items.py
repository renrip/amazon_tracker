from __future__ import print_function

import os.path
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1fYlHIvW5hB1w69aFPSPxCf9cz4l5HM5Pk0ydBietdL8'
# SAMPLE_RANGE_NAME = 'R1C1:R5C3'
SAMPLE_RANGE_NAME = 'sheet1'

class WatchedItems():

    def __init__(self,csv_log_file="watched_items_log.csv") -> None:
        self.loaded = False
        self.items = []
        self.error_msg = None
        self.csv_log_file = csv_log_file
        self.load_list()

    def set_not_loaded_status(self, msg="Default error message"):
        self.loaded = False
        self.items = []
        self.error_msg = msg
        print("Error Msg: " + msg)

    def load_list(self):
        """Load list of items to track via Google Workspace Sheets API.
        All credentials and knowledge of the Google Sheet is encapsulated
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('sheets', 'v4', credentials=creds)

            # Call the Sheets API
            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME).execute()
            values = result.get('values', [])

            if not values:
                self.set_not_loaded_status('Spreadsheet data not retrieved')
                return
            
            # Sanity check the loaded data
            #   - Check first row for expected headings
            #   - setup vars for the rest of the method processing

            # print(f"values: {values}")
            url_index = None
            alert_price_index = None
            first_row = values[0]

            # Check for "group" column in first row
            if "group" in first_row:
                group_index = first_row.index("group")
                # print(f"group_index: {group_index}")
            else:
                self.set_not_loaded_status('"group" column not present')
                return

            # Check for "url" column in first row
            if "url" in first_row:
                url_index = first_row.index("url")
                # print(f"url_index: {url_index}")
            else:
                self.set_not_loaded_status('"url" column not present')
                return
            
            # Check for "desc" column in first row
            if "desc" in first_row:
                desc_index = first_row.index("desc")
                # print(f"url_index: {url_index}")
            else:
                self.set_not_loaded_status('"desc" column not present')
                return            

            # Check for "alert_price" column in first row
            if "alert_price" in first_row:
                alert_price_index = first_row.index("alert_price")
                # print(f"alert_price_index: {alert_price_index}")
            else:
                self.set_not_loaded_status('"alert_price" column not present')
                return

            self.items = []
            max_column = max(url_index, alert_price_index)
            # print(f"max_column: {max_column}")

            for row in values[1:]:
                # print(f"row: {row}")
                if len(row) > max_column:
                    self.loaded = True
                    item_dict = {}
                    item_dict["group"] = row[group_index]
                    item_dict["url"] = row[url_index]
                    item_dict["desc"] = row[desc_index]
                    item_dict["alert_price"] = row[alert_price_index]
                    self.items.append(item_dict)
                else:
                    print(f"Ignoring incoplete item row: {row}")

            # print(f"items[]: {self.items}")

        except HttpError as err:
            self.set_not_loaded_status('HttpError exception:' + "\n" + err)
            return

    def log_file_ready(self)-> bool:

        log_file_path = Path(self.csv_log_file)
        
        if log_file_path.is_file():
            return True
        else:
            try:
                log_file = open(self.csv_log_file, "a")
                log_file.write("group" + "," + "url" + "," + "desc" + "," +
                               "date" + "," + "time" + "," + 
                               "price" + "," + "disc" + "," + "disc_pct" + "," + "price_final" + "," + 
                                "title"+ 
                                "\n")
                log_file.close()
            except:
                return False
            else:
                return True

    def log_item(self, item: dict):
        
        if self.log_file_ready():
            with open(self.csv_log_file, "a") as log_file:

                # trim the "title" to max of 40 chars
                title_max_len = 40
                title = item["title"]
                if len(title) > title_max_len:
                    title = title[:title_max_len]
                
                # also replace coma and quote characters for CSV file happieness
                title = title.replace(',', '.')
                title = title.replace('"', '^')

                log_file.write(item["group"] + "," + 
                               item["url"] + "," +
                               item["desc"] + "," +
                               item["date"] + "," +
                               item["time"] + "," + 
                               str(item["price"]) + "," + 
                               str(item["disc"]) + "," + 
                               str(item["disc_pct"]) + "," + 
                               str(item["price_final"]) + "," + 
                               '"' + title + '"' + "\n"
                               )
                
        else:
            print("Class WatchedItems.log_item(): problem writing to log file")

def main():
    print("--- watched_items.py main() output:")
    wi = WatchedItems()
    print(f"loaded: {wi.loaded}\nitem_count: {len(wi.items)}\nitems: {wi.items}")

    print(f"log_file_ready() method: {wi.log_file_ready()}")

if __name__ == '__main__':
    main()