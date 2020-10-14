#!/usr/bin/env python3
import os
import re
import requests
import OpenSong
import datetime
import json

# GLOBALS
LIBRARY_PATH = '/Volumes/Data/SEAFILE/LCC/LCC Worship Team/OpenSong'
song_details = 'https://reporting.ccli.com/api/detail/song/{}'
report_endpoint = 'https://reporting.ccli.com/api/report'


scriptdir = os.path.dirname(os.path.realpath(__file__))
curl_config_file = os.path.join(scriptdir, 'ccli-curl.config')
historyfile = os.path.join(scriptdir, 'ccli-reporting.json')
history = {}


# if the script doesn't work, you need to re-log into your ccli account,
# perform a search, and then a report and paste the curl command retrieved from
# Chrome Developer Tools into the 'ccli-curl.config' file:
#
# It will be a POST to https://reporting.ccli.com/api/report
tmp = open(curl_config_file, 'r').read()
curlcmd = tmp.replace('\r', '\n').replace('\n\n', '\n').replace('\\\n', ' ')

# parse headers from the curl command
header_pairs = re.findall(r'-H \'(.*?):(.*?)\'', curlcmd)
headers = {}
for k, v in header_pairs:
    headers[k] = v.strip()


def load():
    global history
    if os.path.exists(historyfile):
        history = json.loads(open(historyfile, 'r').read())
    else:
        history = {}


def save():
    open(historyfile, 'w').write(json.dumps(history, indent=2))


def make_report_data(id, title, ccli):
    report_data = {
        "id": "", "date": "",
        "songs": [{"id": id, "title": title, "ccliSongNo": ccli}],
        "recordedBy": {"id": "", "title": ""},
        "lyrics": {"print": 0, "digital": "1", "record": 0, "translate": 0},
        "sheetMusic": [], "rehearsals": [], "masterRecordings": []
    }
    return report_data



# now, here is the real procedure
load()
if 'last_report_timestamp' in history:
    last_report_timestamp = history['last_report_timestamp']
else:
    last_report_timestamp = '2020-10-04'  # october 4, 2020

last_date = last_report_timestamp
today = datetime.date.today().strftime('%Y-%m-%d')

toreport = []
lib = OpenSong.Library(LIBRARY_PATH)
for datestamp in lib.sets:
    songset = lib.sets[datestamp]
    if last_date < songset.name < today:
        print('\nREPORT NEEDED: ' + songset.name)
        for song in songset.songs:
            print(song.name)
            toreport.append({'ccli':song.ccli, 'title': song.name, 'path': song.path})


# setup the session
sess = requests.Session()
sess.headers = headers

for songdata in toreport:
    ccli = songdata['ccli']
    title = songdata['title']
    print(f'GRAB SONG DATA FOR #{ccli}')
    r = sess.get(song_details.format(ccli))
    if r.status_code == 200:
        details = r.json()
        print(f'FOUND DETAILS FOR {details["title"]}... Submitting Report')
        tosubmit = make_report_data(details['id'], details['title'], details['ccliSongNo'])
        r = sess.post(report_endpoint, json=tosubmit)
        print(r.text)

history['last_report_timestamp'] = today
history[today] = toreport
save()
