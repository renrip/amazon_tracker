import time, json, sys, getopt
# import requests
# from bs4 import BeautifulSoup
# import lxml
# from datetime import datetime as dt

from watched_items import WatchedItems
from my_messaging import send_twilio_message

def main():

    # print(f"sys,argv: {sys.argv}")

    log_file = None

    argumentList = sys.argv[1:]

    # TODO Add option to load watched items from file (default="watched_items.json")
    options = "l:i:"

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argumentList, options)
        # print(arguments)
        # print(values)

        # checking each argument
        for currentArgument, currentValue in arguments:
    
            if currentArgument in ("-l"):
                log_file = currentValue
                print(f"Will log to: {log_file}")
            else:
                print(f"Unexpected arg ({currentArgument} {currentValue}): ignored")
                
        if len(values) > 0:
            print(f"Unexpected value(s): {values} : ignored")
        
    except getopt.error as err:
        # output error, and return with an error code
        print (str(err))

    # Options gathered. Min code starts below

    if log_file :
        wi = WatchedItems(log_file)
    else:
        wi = WatchedItems()

    wi.load_list();

    watched_items = wi.items

    items_logged = 0

    for item in watched_items:

        row = wi.scrape_item(item)

        # only alert for completely "clean" scrapes
        if row["scrape_status"] and row["keywords_status"]:
            if row["price_final"] <= row['alert_price']:
                alert_string = f"{item['url']} ({item['desc']}) is now ${row['price_final']}"
                print(alert_string)
                try:
                    send_twilio_message(alert_string)
                except:
                    print("main(): Sending Twillow message failed")

        # Warn about missing keywords
        if not row["keywords_status"]:
            print(f"main(): Warning - keywords missing: {row['keywords_missing']}")

        # keywords errors can be ignored for logging purposes. This will help debugging.
        # TODO See if history.py needs to be made smarter for this design choice
        if row["scrape_status"]:
            if wi.log_item(row) == True:
                items_logged += 1

        time.sleep(3)

    print(f"Logged {items_logged} of {len(watched_items)} items")    

if __name__ == '__main__':
    main()