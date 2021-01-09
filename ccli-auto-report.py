#!/usr/bin/env python3
import os
import re
import requests
import OpenSong
import datetime
import json

# CONFIGURATION
# if the script doesn't work, you need to re-log into your ccli account,
# perform a search, and then a report and paste the curl command retrieved from
# Chrome Developer Tools into the 'ccli-curl.config' file:
#
# It will be a POST to https://reporting.ccli.com/api/report



# GLOBALS
LIBRARY_PATH = '/Volumes/Data/SEAFILE/LCC/LCC Worship Team/OpenSong'
song_details = 'https://reporting.ccli.com/api/detail/song/{}'
report_endpoint = 'https://reporting.ccli.com/api/report'
search_endpoint = 'https://reporting.ccli.com/api/search?searchCategory=all&searchFilters=[]&searchTerm='

scriptdir = os.path.dirname(os.path.realpath(__file__))
curl_config_file = os.path.join(scriptdir, 'ccli-curl.config')
historyfile = os.path.join(scriptdir, 'ccli-reporting.json')
history = {}

# setup the session
sess = requests.Session()

def setup_session():
    global sess
    tmp = open(curl_config_file, 'r').read()
    curlcmd = tmp.replace('\r', '\n').replace('\n\n', '\n').replace('\\\n', ' ')

    # parse headers from the curl command
    header_pairs = re.findall(r'-H \'(.*?):(.*?)\'', curlcmd)
    headers = {}
    for k, v in header_pairs:
        headers[k] = v.strip()
    sess.headers = headers


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

def song_search(title):
    url = f'{search_endpoint}{title.replace(" ","+")}'
    r = sess.get(url)
    songs = []
    if r.status_code == 200:
        data = r.json()
        songs = data['results']['songs']
    return songs

def ccli_from_title(title):
    songs = song_search(title)
    if len(songs) == 0:
        ccli = input(f'Enter a CCLI number for this song: {title}\n> ')
        return ccli if ccli != '' else None
    elif len(songs) == 1:
        return songs[0]['ccliSongNo']
    
    print('SELECT THE CORRECT SONG:')
    for index, song in enumerate(songs):
        print(f'{index+1} : {song["title"]} by {",".join(song["authors"])}')
        i = input(f'\nWhich number is correct? (Leave blank to skip this song)\n> ')
        if i == '':
            return None
        else:
            i = int(i)
            if 0 < i <= len(songs):
                return songs[i-1]['ccliSongNo']
    return None

# now, here is the real procedure
load()
setup_session()

if 'last_report_timestamp' in history:
    last_report_timestamp = history['last_report_timestamp']
else:
    last_report_timestamp = '2020-10-04'  # october 4, 2020

last_date = last_report_timestamp
today = datetime.date.today().strftime('%Y-%m-%d')

toreport = []
print(f'Looking for unreported sets in {LIBRARY_PATH}')
lib = OpenSong.Library(LIBRARY_PATH)
for datestamp in lib.sets:
    songset = lib.sets[datestamp]
    if last_date < songset.name < today:
        print('\nREPORT NEEDED: ' + songset.name)
        for song in songset.songs:
            if 'ALTERNATES' in song.name:
                break
            print(song.name)
            toreport.append({'ccli':song.ccli, 'title': song.name, 'path': song.path})



if len(toreport) == 0:
    print('Nothing to report.')
    exit()

else:
    for songdata in toreport:
        title = songdata['title']
        print(f'PREPARING TO REPORT: {title}')
        ccli = songdata['ccli']
        if ccli is None:
            ccli = ccli_from_title(title)
        if ccli is None:
            continue
        r = sess.get(song_details.format(ccli))
        print(f'GRAB SONG DATA FOR {title} (#{ccli})')
        if r.status_code == 200:
            details = r.json()
            print(f'FOUND DETAILS FOR {details["title"]}... Submitting Report')
            tosubmit = make_report_data(details['id'], details['title'], details['ccliSongNo'])
            r = sess.post(report_endpoint, json=tosubmit)
            print(r.text)
        else:
            print('failed... please report this song manually and then update your configuration')
            print('visit this page and login: https://reporting.ccli.com/search')
            print('open dev tools, and switch to network tab')
            print(f'search for {title} in the search box')
            print('report that it was used')
            print('in dev tools look for the line that just says "report"')
            print(f'copy that command as a CURL and paste it here {curl_config_file}')
            os.system(f'mate "{curl_config_file}"')
            input('hit return when you are done: ')
            setup_session()

    history['last_report_timestamp'] = today
    history[today] = toreport
    save()
