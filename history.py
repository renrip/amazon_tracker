import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Load raw data
df = pd.read_csv("watched_items_log.csv")
print(f"LEN-raw: {len(df)}")
# print(df)

# clean duplicates based on url,date, and final_price
df = df.drop_duplicates(subset=['url','date','price_final'])
print(f"LEN-clean: {len(df)}")
# print(df)

# get list of unique url vals. Use as the item index
urls = df.url.unique()
print(f"LEN-urls: {len(urls)}\n {urls}")

# get list of unique groups. use to group items into plots
groups = df.group.unique()
print(f"LEN-groupss: {len(groups)}\n {groups}")

# Build a dict () of dataframes split by the url (url is dict index)
item_prices = {}
for url in urls[0:]:
    df_url = df.loc[df["url"] == url]
    item_prices[url] = df_url
    # print(f"{len(df_url)} unique prices for item {url}")
    # print(df_url)

# Build a dict of dataframes split by the url (url is dict index)
# item_groups = {}
# for url in urls[0:]:
#     df_group = df.loc[df["group"] == url]
#     item_groups[url] = df_group
#     print(f"{len(df_group)} unique groups for url {url}")
#     print(df_group)

# print(f"item_prices type: {type(item_prices)}\n {item_prices}")

# TODO Figure out a way to group like things. Keys in desc?
#      will have to collect data sets into lists/dict and then
#      display after looping

# TODO figure out how to make legend for the y data sets
ax = None
# Build and display scatter plot(s)
for key in item_prices:
    # ax = plt.subplots()
    
    # print(f"item type: {type(item_prices[key])}\n {item_prices[key]}")
    # print(item_prices[key][-1:].group.item())
    # print(item_prices[key][-1:])
    # print(item_prices[key])
    item_group = str(item_prices[key][-1:].group.item())
    item_desc = str(item_prices[key][-1:].desc.item())
    if item_group == "computers":
        if ax == None:
            ax = plt.subplot()
            plt.title(item_group)
        ax.scatter(list(item_prices[key].date.values), 
                    list(item_prices[key].price_final.values),
                    label=item_desc)
    else:
        continue
        # ax.scatter(list(item_prices[key].date.values), 
        #             list(item_prices[key].price_final.values))

    plt.xticks(rotation=60, ha='right')

    # Use the last rows value of 'desc'
    # Updating the spreadsheet will ultimately change the plot title
    # Also get the url from that row just for consistency
    # plt.title(item_prices[key][-1:].desc.item() + 
    #           "\n(" + item_prices[key][-1:].url.item() + ")")
    
    

    # Put these in the loop for 1-by-1 or here for all together.
    ax.legend()
    
    plt.tight_layout()
plt.show()    
