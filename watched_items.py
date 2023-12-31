from __future__ import print_function

import os
import os.path
from pathlib import Path
from datetime import datetime as dt
import requests
from bs4 import BeautifulSoup
import lxml

from my_messaging import send_twilio_message

# Google Workspace imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Workspace setup
# TODO figure out how to do writes to Sheets docs
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

google_client_id= os.environ.get("GOOGLE_CLIENT_ID")
google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

google_client_config = {
    "installed": {
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": ["http://localhost"],
        "project_id": "my-cloud-sheets",
        "client_id": google_client_id,
        "client_secret": google_client_secret
    }
}

# The ID and range of the WatchedItems Sheets doc
SPREADSHEET_ID = '1fYlHIvW5hB1w69aFPSPxCf9cz4l5HM5Pk0ydBietdL8'
RANGE_NAME = 'sheet1'


browser_headers = {
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


class WatchedItems():

    def __init__(self, csv_log_file="watched_items_log.csv") -> None:
        self.loaded = False
        self.items = []
        self.error_msg = None
        self.csv_log_file = csv_log_file

    def set_not_loaded_status(self, msg="Unspecified"):
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
        else:
            print("WatchedItems.load_list(): No stored Google creds (token.json)")

        # TODO recreating the token.json file does not work now that my project 
        #      (my-cloud-sheets) is public. Fix by deleting the token.json and 
        #      chasing cheese

        # If there are no (valid) credentials available, let the user log in.
        try:
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    #print("WatchedItems.load_list(): Goggle creds expired, refreshing")
                    creds.refresh(Request())
                else:
                    print("WatchedItems.load_list(): Creating Goggle creds")
                    flow = InstalledAppFlow.from_client_config(google_client_config, SCOPES)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

        except Exception as inst:
            # hopefully this is very rare
            send_twilio_message(f"WatchedItems.load_list(): Unexpected Exception type:{type(inst)=}")
            print("WatchedItems.load_list(): Exception during Google Workspace setup")
            print(f"Unexpected {inst=}, {type(inst)=}")
            exit(-1)

        try:
            service = build('sheets', 'v4', credentials=creds)

            # Call the Sheets API
            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
            values = result.get('values', [])

            if not values:
                self.set_not_loaded_status('Spreadsheet data not retrieved')
                return
            
            # print(f"values: {values}")

            first_row = values[0]
            indices = [] # Build this to find the max index of our required columns

            # Check for required columns
            if "group" in first_row and \
                "url" in first_row and \
                "desc" in first_row and \
                "alert_price" in first_row:
                group_index = first_row.index("group")
                indices.append(group_index)
                url_index = first_row.index("url")
                indices.append(url_index)
                desc_index = first_row.index("desc")
                indices.append(desc_index)
                alert_price_index = first_row.index("alert_price")
                indices.append(alert_price_index)
                # Grab indexes of optional colums
                if "keywords" in first_row:
                    keywords_index = first_row.index("keywords")
                else:
                    keywords_index = None
            else:
                self.set_not_loaded_status('Not all required columns present')
                return

            # Build a list of items (dicts)
            self.items = []
            max_column = max(indices)
            # print(f"max_column: {max_column}")

            for row in values[1:]:
                # print(f"row: {row}")
                # Checking this allows us to simply ignore incomplete rows
                # rather than letting weird data blow us up
                if len(row) > max_column:
                    self.loaded = True
                    item_dict = {}
                    item_dict["group"] = row[group_index]
                    item_dict["url"] = row[url_index]
                    item_dict["desc"] = row[desc_index]
                    item_dict["alert_price"] = row[alert_price_index]
                    # Add optional elements
                    if keywords_index and keywords_index < len(row) and type(row[keywords_index]) == str:
                        item_dict["keywords"] = row[keywords_index].split()
                    # Put it on the list of items
                    self.items.append(item_dict)

                elif len(row) > 0:
                    print(f"Ignoring incoplete item row: {row}")

                # Quietly ignore empty rows

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
    def validate_amazon_item(self, item: dict, row: dict, soup: BeautifulSoup):
        avail_div = soup.find(id="availability_feature_div")
        if avail_div:
            spans = avail_div.find_all("span")
            for s in spans:
                if "unavailable" in s.getText():
                    row["scrape_status"] = False
                    row["scrape_error"] = "Appears Unavailable"
                    return False
                                    
        return True
    
    def scrape_amazon_item(self, item: dict, row: dict):

        # print(f"CHECKING: {item['url']} ({item['desc']})")

        # Create Beautiful Soup object first to pass to the validation method
        # TODO try/catch rather than just raising 
        response = requests.get(item["url"], headers=browser_headers)
        # print(f"HTTP Status: {response.status_code}")

        response.raise_for_status()

        # soup = BeautifulSoup(response.text, "html.parser")
        soup = BeautifulSoup(response.text, "lxml")
        # print(soup)

        # return empty row (error) if validation tests not passed
        if not self.validate_amazon_item(item, row, soup):
            return row
        
        timestamp = dt.now()
        row["date"] = timestamp.strftime("%Y-%m-%d")
        row["time"] = timestamp.strftime("%H:%M:%S")


        row["group"] = item['group']
        row["url"] = item['url']
        row["desc"] = item['desc']
        row["alert_price"] = float(item['alert_price'])

        product_title = soup.select_one(selector="#productTitle").getText().strip()
        # print(product_title)

        # print(f"PRODUCT_TITLE: {product_title}")
        row["title"] = product_title

        price_whole = soup.find(name="span", class_="a-price-whole").getText()
        price_fraction = soup.find(name="span", class_="a-price-fraction").getText()
        price = float(price_whole + price_fraction)

        # print(f"WHOLE|FRACTION: {price_whole}|{price_fraction}")
        # print(f"PRICE: {price}")
        row["price"] = price

        discount = 0
        discount_percent = 0

        labels = soup.find_all(name="label")
        for l in labels:
            splits = l.getText().split()
            if len(splits) > 0 and splits[0] == "Apply" and splits[2] == "coupon":
                # print(f"LABEL_SPLITS: {splits}")
                if splits[1][0] == "$":
                    discount = float(splits[1][1:])
                    break
                elif splits[1][-1] == "%":
                    discount_percent = float(splits[1][:-1])
                    break

        # print(f"DISCOUNT: {discount}")
        row["disc"] = discount
        # print(f"DISCOUNT_percent: {discount_percent}")
        row["disc_pct"] = discount_percent

        price_final = price - discount

        if discount_percent > 0:
            price_final = price_final * (1 - discount_percent/100)
        
        price_final = round(price_final, 2)

        # print(f"PRICE_FINAL: {price_final}")

        row["price_final"] = price_final

        # Check for keywords and set appropriate status
        if "keywords" in item:
            for kw in item["keywords"]:
                if kw not in row["title"]:
                    row["keywords_status"] = False
                    row["keywords_missing"].append(kw)

        return row


    def scrape_item(self, item: dict):
        # setup clean statuses. Pass this "return value / row" around the scraping methods
        row = {"scrape_status": True,
               "scrape_error": None,
               "keywords_status": True,
               "keywords_list": []}


        if "www.amazon.com" in item["url"]:
            row = self.scrape_amazon_item(item, row)
        else:
            row["scrape_status"] = False
            row["scrape_error"] = f"Unsupported web site specified in URL: {item['url']}"

        return row

    def log_item(self, item: dict):
        
        if self.log_file_ready():
            with open(self.csv_log_file, "a") as log_file:

                # Replace bad chars for CSV output in desc
                # so the user does not have to think about this in the spreadsheet
                desc = item["desc"]
                desc = desc.replace(',', '.')
                desc = desc.replace('"', '^')

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
                               desc + "," +
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
            return False
    
        return True

def main():
    print("--- watched_items.py main() output:")
    wi = WatchedItems()
    print(f"loaded: {wi.loaded}\nitem_count: {len(wi.items)}\nitems: {wi.items}")

    print(f"log_file_ready() method: {wi.log_file_ready()}")

if __name__ == '__main__':
    main()