import time, json, sys, getopt, os
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# print(f"sys,argv: {sys.argv}")

# deply default opts
user_opts = {
    "silent_mode": False ,
    "plot_dir": "./" ,
    "maint_mode": False ,
    "log_file": "watched_items_log.csv" ,
    "compress": False ,
    "yes_mode": False ,
    }

# override user_opts stuff for dev/testing
# ******** COMMENT these BEFORE commiting ******
# user_opts["silent_mode"] = True
# user_opts["plot_dir"] = "./images"
user_opts["log_file"] = "cron_items_log.csv"
user_opts["maint_mode"] = True
user_opts["compress"] = True
# user_opts["yes_mode"] = True
# user_opts["trim"] = "TESTING"

USAGE = """Usage: python3 history.py <options>\n\
Tool to analyze, visualize, and maintain log_file created by main.py\n
Options:\n
    -s Silent mode. Quietly saves analysis plots to '-d ' directory
    -d <directory> to write plots to. (default "./")
    -m Maintenance operations (-c, -t) only. Do not analyze log_file
    -l <log file name> to analyze or mainta== default "watched_items_log.csv")
    -c Compress log file (removes redundant entries from the log file)
    -t <string> Trim log file rows with <string> as 'group' or within 'url'
    -y YES mode. Do trim operations without prompting
    -h Help"""


def analyzer():
    # Load raw data
    # Could wrap in a try block but I'd probably just print the error and return/exit anyway
    df = pd.read_csv(user_opts["log_file"])
    # print(f"LEN-raw: {len(df)}")
    # print(df)

    # clean duplicates based on url,date, and final_price (and group)

    # had to add group because if group gets added mid-day then dropping
    # duplicates without considering group would choose the earlier one without it.
    # perhaps ther is a better solution, like grabbing the group earlier?
    df = df.drop_duplicates(subset=['group','url','date','price_final'])
    # print(f"LEN-clean: {len(df)}")
    # print(df)

    # get list of unique url vals. Use as the item index
    urls = df.url.unique()
    # print(f"LEN-urls: {len(urls)}\n {urls}")

    # get list of unique groups. use to group items into plots
    groups_df = df.group.unique()
    # print(f"groups_df type/len()/value: {type(groups_df)}/{len(groups_df)}/{groups_df}")

    # only keep str rows (Pandas puts a float/NaN when a column value is not present)
    groups = [g for g in groups_df if type(g) is not float]
    # print(f"groups type/len()/value: {type(groups)}/{len(groups)}/{groups}")



    # Build a dict () of dataframes split by the url (url is dict index)
    item_prices = {}
    for url in urls:
        df_url = df.loc[df["url"] == url]
        item_prices[url] = df_url
        # print(f"{len(df_url)} unique prices for item {url}")
        # print(df_url)

    # print(f"item_prices type: {type(item_prices)}\n {item_prices}")


    for g in groups:
        # print("operating on a group")
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

        if user_opts["silent_mode"] == True:
            today = datetime.now()
            today_str = today.strftime("%Y%d%m")
            # save with a date uniquifier, overwrite any from earlier in the day
            # print(f"Saving plt to:")
            # print(f"{user_opts['plot_dir']}{g}_{today_str}.png")
            plt.savefig(f"{user_opts['plot_dir']}{g}_{today_str}.png")
            plt.close()
            ax = None
        else:
            plt.show()

    # now make single item plots for un grouped items

    # Build and display scatter plot(s)
    for key in item_prices:
        # print("operating on a singleton")
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
                plt.title(item_desc)
            ax.scatter(list(item_prices[key].date.values), 
                        list(item_prices[key].price_final.values))
        else:
            # print("failed the item in a group test")
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
        # ax.legend()
        
        plt.tight_layout()

        if user_opts["silent_mode"] == True:
            # create uniquifier to append to logfile base name
            today = datetime.now()
            today_str = today.strftime("%Y%d%m")

            # Replace bad chars for filename in desc
            # so the user does not have to think about this in the spreadsheet
            item_desc_base = item_desc
            item_desc_base = item_desc_base.replace(' ', '_')
            item_desc_base = item_desc_base.replace('.', '_')

            # save with a date uniquifier, overwrite any from earlier in the day
            # print("Saving singleton plot to:")
            # print(f'{user_opts["plot_dir"]}{item_desc_base}_{today_str}.png')
            plt.savefig(f'{user_opts["plot_dir"]}{item_desc_base}_{today_str}.png')
            plt.close()
            ax = None
        else:
            plt.show()

def compressor(df):
    """load csv, trim to unique on
    url,date,price,disc,disc_pct,price_final"""

    print("Entering - compressor()")

    # df = pd.read_csv(user_opts["log_file"])
    len_orig = len(df)
    print(f"compressor(): starting log size is {len(df)} rows")
    # print(f"LEN-raw: {len_orig}")
    # print(df)

    df_clean = df.drop_duplicates(subset=['url','date','disc','disc_pct','price_final'], keep="last")
    len_clean = len(df_clean)
    # print(f"LEN-clean: {len_clean}")
    # print(df_clean)

    # nothing to do. return
    if len_orig == len_clean:
        print("compressor(): The log is already compressed")
        return df

    print(f"compressor(): removed {len(df) - len(df_clean)} rows")

    return df_clean


def trimmer(keyword :str, df):
    print(f"Entering trimmer(): keyword: \"{keyword}\"")
    print(f"Checking for \"{keyword}\" in group column...")
    print(f"LEN-start: {len(df)}")

    orig_df_len = len(df)

    # filter rows without a value in 'group' column
    df_notna_group = df[df['group'].notna()]
    # print(f"LEN-notna-group: {len(df_notna_group)}")

    # pick rows with keyword as group
    df_match_group = df_notna_group[df_notna_group['group'].str.match(keyword)]
    # print(f"LEN-match-group: {len(df_match_group)}")

    if len(df_match_group) > 0:
        if user_opts["yes_mode"] == True:
            resp = 'y'
        else:
            resp = input(f"Found {len(df_match_group)} rows with group == \"{keyword}\"\nDelete these? (y,n)")
    else:
        resp = 'n'

    if resp == 'y':
        indices_to_drop = df_match_group.index.values.tolist()
        # print(f"indices: {indices_to_drop}")
        df_final = df.drop(index=indices_to_drop)
        print(f"LEN-final: {len(df_final)}")
        return(df_final)
    else:
        print(f"Checking for \"{keyword}\" in url column...")

    print(f"LEN-start: {len(df)}")
    # print(df)
    df_match_url = df[df['url'].str.contains(keyword)]
    # print(f"LEN-match-url: {len(df_match_url)}")

    if len(df_match_url) > 0:
        if user_opts["yes_mode"] == True:
            resp = 'y'
        else:
            resp = input(f"Found {len(df_match_url)} rows where url contains \"{keyword}\"\nDelete these? (y,n)")
    else:
        resp = 'n'

    if resp == 'y':
        indices_to_drop = df_match_url.index.values.tolist()
        # print(f"indices: {indices_to_drop}")
        df_final = df.drop(index=indices_to_drop)
        print(f"LEN-final: {len(df_final)}")
        return(df_final)
    else:
        return(df)

    
def main():
    argumentList = sys.argv[1:]
    options = "sd:ml:ct:hy"
    options_tester = ["-s", "-d", "-m", "-l", "-c", "-t", "-h", "-y"]

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argumentList, options)
        # print(arguments)
        # print(values)

        # checking each argument
        for currentArgument, currentValue in arguments:


            if currentArgument not in options_tester:
                print(f"main(): option {currentArgument} not recognized")
                continue

            elif currentArgument == "-s":
                user_opts["silent_mode"] = True

            elif currentArgument == "-d":
                user_opts["plot_dir"] = currentValue
                # TODO Sanity test '-d' option value

            elif currentArgument == "-m":
                user_opts["maint_mode"] = True

            elif currentArgument == "-l":
                user_opts["log_file"] = currentValue

            elif currentArgument == "-c":
                user_opts["compress"] = True

            elif currentArgument == "-t":
                user_opts["trim"] = currentValue
                
            elif currentArgument == "-h":
                print(USAGE)
                exit(0)

            elif currentArgument == "-y":
                user_opts["yes_mode"] = True

        if len(values) > 0:
            print(f"Unexpected value(s): {values} : ignored")
            exit() # should raise exception
        
    except getopt.error as err:
        # output error, and return with an error code
        print (str(err))
        print(USAGE)
        exit(-1)

    else:
        # break out log_file (path, basename, extension) components
        # TODO test with log_file values with (paths, multi '.', spaces, others?)
        if "log_file" in user_opts:
            user_opts["log_file_path"] = os.path.dirname(user_opts["log_file"])
            # if there is a path, add the trailing '/' now
            if len(user_opts["log_file_path"]):
                user_opts["log_file_path"] += '/'
            split_name = os.path.splitext(os.path.basename(user_opts["log_file"]))
            split_name_len = len(split_name)
            if split_name_len > 0:
                user_opts["log_file_basename"] = split_name[0]
            if split_name_len > 1:
                user_opts["log_file_extension"] = split_name[-1]
            # TODO if this can happen code to handle it
            if split_name_len > 2:
                print(f"main(): Problem processing log_file name \"{user_opts['log_file']}\"") 
                exit(-1)
        
        # add a '/' to the end of the plot_dir if it doesnt have one
        if "plot_dir" in user_opts:
            if user_opts["plot_dir"][-1] != '/':
                user_opts["plot_dir"] += '/'

        print(f"user_opts: {user_opts}")



    ### Options gathered. Main code starts below

    # pull the log_file into a DataFrame
    df = pd.read_csv(user_opts["log_file"])

    # save original len to test for deletions later
    orig_log_file_len = len(df)

    # perform compress and trim operations prior to analyzing
    if "compress" in user_opts and user_opts["compress"] == True:
        df = compressor(df)

    if "trim" in user_opts:
        df = trimmer(user_opts["trim"], df)

    # Backup,update log_file to file system (if compressed or trimmed)
    if len(df) < orig_log_file_len:
        now = datetime.now()
        now_str = now.strftime("%Y%d%m_%H%M%S")
        backup_fullname = user_opts["log_file_path"] + user_opts["log_file_basename"] + \
                        '_' + now_str + user_opts["log_file_extension"]

        # Make backup of current log_file
        if os.path.isfile(user_opts["log_file"]):
            os.rename(user_opts["log_file"], backup_fullname)
            print(f"Backed up log gile to: {backup_fullname}")

        # Write new log_file
        df.to_csv(user_opts["log_file"], index=False, mode="w")
        print(f"Updated log with {len(df)} lines")

    # Run the analyzer on the updated logfile (only if not in maint_mode)
    if not user_opts["maint_mode"]:
        analyzer()

if __name__ == '__main__':
    main()
