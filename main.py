import time, json, sys, getopt
import requests
from bs4 import BeautifulSoup
import lxml
from datetime import datetime as dt

from watched_items import WatchedItems




browser_headers = {
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
}

def main():

    # print(f"sys,argv: {sys.argv}")

    log_file = None

    argumentList = sys.argv[1:]
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

    watched_items = wi.items

    # collected rows not used anymore. logged one by one
    # leaving in in case I want to add a batch loggin method.
    output = []

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

        print(f"CHECKING: {item['url']} ({item['desc']})")

        response = requests.get(item["url"], headers=browser_headers)
        # print(f"HTTP Status: {response.status_code}")
        response.raise_for_status()

        # soup = BeautifulSoup(response.text, "html.parser")
        soup = BeautifulSoup(response.text, "lxml")

        product_title = soup.select_one(selector="#productTitle").getText().strip()

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
            print(f"{row['desc']} ({row['url']}) is at or below it's alert_price")

        output.append(row)

        wi.log_item(row)

        time.sleep(5)
        
    # Now logging one by one in the loop above
    # for row in output:
    #     print(f"row: {row}")
    #     wi.log_item(row)



if __name__ == '__main__':
    main()