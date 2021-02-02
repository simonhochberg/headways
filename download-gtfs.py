# This script downloads all GTFS data available on transitfeeds.com via API
# This script is still a work in progress

import csv
import datetime
import json
import os
import requests 
import shutil
import time
import zipfile

# download list of agency IDs from transit feeds

listOfAgencyIDs = []
api_key = "94413ac9-aec7-4720-a731-640e98d65763" # this is my API key; replace with your own
r_url = f"https://api.transitfeeds.com/v1/getFeeds?key={api_key}&location=67&descendants=1&limit=100"
r = requests.get(r_url)

# This sequence checks to see if a JSON with the last update times exists
# if it does, the JSON is loaded and any additional feeds are added to the file
# if it does not, the JSON is created

last_update_times_exists = os.path.exists("last_update_times.json")

if last_update_times_exists:
    with open('last_update_times.json', 'r') as fp:
        last_update_times = json.load(fp)
        for feed in r.json()["results"]["feeds"]:
            if feed["id"] not in last_update_times:
                last_update_times[feed["id"]] = feed["latest"]["ts"]
            else:
                pass
        with open('last_update_times.json', 'w') as fp:
            json.dump(last_update_times, fp)
else:
    # Build the last_update_times.json file
    last_update_times = {}
    for feed in r.json()["results"]["feeds"]:
        try:
            last_update_times[feed["id"]] = feed["latest"]["ts"]
        except KeyError:
            last_update_times[feed["id"]] = 0
    with open('last_update_times.json', 'w') as fp:
        json.dump(last_update_times, fp)

numPages = r.json()["results"]["numPages"] # capture all gtfs feeds 

for page in range(1,(numPages+1)):
    url = r_url + "&page={}".format(str(page)) # pass page argument to API url
    r = requests.get(url)
    for feed in (r.json()["results"]["feeds"]):
        if feed["ty"] == "gtfs" and feed["id"] not in listOfAgencyIDs:
            listOfAgencyIDs.append(feed["id"]) # append GTFS feed to list of desired feeds

# download zipped GTFS data for each agency
for feed in listOfAgencyIDs:
    url = f"https://api.transitfeeds.com/v1/getLatestFeedVersion?key={api_key}&feed={feed}"
    g = requests.get(url)
    slashRemoval = "--".join(feed.split("/"))
    filename = "{}.zip".format(slashRemoval)
    with open(filename, "wb") as fd:
        for chunk in g.iter_content(chunk_size=128):
            fd.write(chunk)
            
# unzip downloaded GTFS data in a new directory called "gtfs"
for feed in listOfAgencyIDs:
    slashRemoval = "--".join(feed.split("/"))
    path = f"{slashRemoval}.zip"
    new_path = "gtfs/{}".format(slashRemoval)
    try:
        zip_ref = zipfile.ZipFile(path, "r")
        zip_ref.extractall(new_path)
        zip_ref.close()
        os.remove(path)
    except:
        print(path)
        os.remove(path)


note_to_write = f"downloaded from https://transitfeeds.com on {str(datetime.date.today())}"
with open("gtfs/README.txt", "w") as text_file:
    text_file.write(note_to_write) 
