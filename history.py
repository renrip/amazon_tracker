import time, json, sys, getopt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# print(f"sys,argv: {sys.argv}")

run_mode_values = ["i", "s", "c"]
user_opts = {"log_file": "watched_items.log.csv",
                "run_mode": "i"}

argumentList = sys.argv[1:]
options = "l:m:"

try:
    # Parsing argument
    arguments, values = getopt.getopt(argumentList, options)
    # print(arguments)
    # print(values)

    # checking each argument
    for currentArgument, currentValue in arguments:

        if currentArgument in ("-l"):
            if type(currentValue) == str and len(currentValue) == 0:
                print("log_file (-l) option must have a value")
            else:
                user_opts["log_file"] = currentValue
            # print(f"Will log to: {user_opts['log_file']}")

        elif currentArgument in ("-m"):
            if currentValue in run_mode_values:
                user_opts["run_mode"] = currentValue
            else:
                print(f"run_mode '{currentValue}' not expected. (i=interactive, s=silent, c=cleanup)")
            # print(f"run_mode is: {user_opts['run_mode']}")

        else:
            print(f"Unexpected arg ({currentArgument} {currentValue}): ignored")
            
    if len(values) > 0:
        print(f"Unexpected value(s): {values} : ignored")

    print(f"run_mode: {user_opts['run_mode']}")
    print(f"log_file: {user_opts['log_file']}")
    
except getopt.error as err:
    # output error, and return with an error code
    print (str(err))


# Options gathered. Min code starts below


# Load raw data
df = pd.read_csv("watched_items_log.csv")
print(f"LEN-raw: {len(df)}")
# print(df)

# clean duplicates based on url,date, and final_price (and group)

# had to add group because if group gets added mid-day then dropping
# duplicates without considering group would choose the earlier one without it.
# perhaps ther is a better solution, like grabbing the group earlier?
df = df.drop_duplicates(subset=['group','url','date','price_final'])
print(f"LEN-clean: {len(df)}")
# print(df)

# get list of unique url vals. Use as the item index
urls = df.url.unique()
print(f"LEN-urls: {len(urls)}\n {urls}")

# get list of unique groups. use to group items into plots
groups_df = df.group.unique()
print(f"groups_df type/len()/value: {type(groups_df)}/{len(groups_df)}/{groups_df}")

# only keep str rows (Pandas puts a float/NaN when a column value is not present)
groups = [g for g in groups_df if type(g) is not float]
print(f"groups type/len()/value: {type(groups)}/{len(groups)}/{groups}")



# Build a dict () of dataframes split by the url (url is dict index)
item_prices = {}
for url in urls:
    df_url = df.loc[df["url"] == url]
    item_prices[url] = df_url
    # print(f"{len(df_url)} unique prices for item {url}")
    # print(df_url)

# print(f"item_prices type: {type(item_prices)}\n {item_prices}")

# TODO Figure out a more elegant way to loop and separate plots
# TODO Figure out how to dump plots to filesystem rather than display
# TODO Impl different run modes, configurable via command line options

for g in groups:

    ax = None
    # Build and display scatter plot(s)
    for key in item_prices:
        
        # print(f"item type: {type(item_prices[key])}\n {item_prices[key]}")
        # print(item_prices[key][-1:].group.item())
        # print(item_prices[key][-1:])
        # print(item_prices[key])

        # 'group' and 'desc' values of last row are used
        # this lets the latest values from the log.guide plot generation
        item_group = str(item_prices[key][-1:].group.item())
        item_desc = str(item_prices[key][-1:].desc.item())
        if item_group == g:
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

    if user_opts["run_mode"] == "s":
        plt.savefig(f"./images/{g}.png")
        plt.close()
        ax = None
    else:
        plt.show()

# now make single item plots for un grouped items

# Build and display scatter plot(s)
for key in item_prices:
    ax = None
    # print(f"item type: {type(item_prices[key])}\n {item_prices[key]}")
    # print(item_prices[key][-1:].group.item())
    # print(item_prices[key][-1:])
    # print(item_prices[key])

    # 'group' and 'desc' values of last row are used
    # this lets the latest values from the log.guide plot generation
    item_group = str(item_prices[key][-1:].group.item())
    item_desc = str(item_prices[key][-1:].desc.item())
    if item_group not in groups:
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

