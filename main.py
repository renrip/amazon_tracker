import time, json, sys, getopt
import requests
from bs4 import BeautifulSoup
import lxml
from datetime import datetime as dt

from watched_items import WatchedItems
from my_messaging import send_twilio_message





browser_headers = {
    "Accept-Language": "en-US,en;q=0.9",
    # "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    # "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    # Amazon started sending "no robots" page with the previous string. works fine with newer one.
    # Do they notice requests from different Chrome versions from the same IP? (works for now)
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

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

    # TODO encapsulate scraping to class. Use URL to know which site and how to scrape
    # TODO Add internal scraping utils to notice/alert on bot rejection or other testable failures.
    
    for item in watched_items:
        # print(item)
        row = {}
        timestamp = dt.now()
        row["date"] = timestamp.strftime("%Y-%m-%d")
        row["time"] = timestamp.strftime("%H:%M:%S")


        row["group"] = item['group']
        row["url"] = item['url']
        row["desc"] = item['desc']
        row["alert_price"] = float(item['alert_price'])

        # print(f"CHECKING: {item['url']} ({item['desc']})")

        response = requests.get(item["url"], headers=browser_headers)
        # print(f"HTTP Status: {response.status_code}")
        response.raise_for_status()

        # soup = BeautifulSoup(response.text, "html.parser")
        soup = BeautifulSoup(response.text, "lxml")
        # print(soup)

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

        if price_final <= row['alert_price']:
            alert_string = f"{item['url']} ({item['desc']}) is now ${price_final}"
            print(alert_string)
            try:
                send_twilio_message(alert_string)
            except:
                print("main(): Sending Twillow message failed")

        # if keywords are not present in the item title, print a warning and don't log the item
        ignore_item = False
        if "keywords" in item:
            for kw in item["keywords"]:
                if kw not in row["title"]:
                    print(f"Keyword: '{kw}' not found in item title:\n{item['url']} ({product_title}")
                    ignore_item = True

        if not ignore_item:
            if wi.log_item(row) == True:
                items_logged += 1

        time.sleep(3)

    print(f"Logged {items_logged} of {len(watched_items)} items")    

if __name__ == '__main__':
    main()