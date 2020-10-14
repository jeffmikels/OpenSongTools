#!/usr/bin/env python3
import os
import re
import requests
import OpenSong
import datetime
import json

history = {}
historyfile = 'ccli-reporting.json'


def load():
    global history
    if os.path.exists(historyfile):
        history = json.loads(open(historyfile, 'r').read())
    else:
        history = {}


def save():
    open(historyfile, 'w').write(json.dumps(history))


def make_report_data(id, title, ccli):
    report_data = {
        "id": "", "date": "",
        "songs": [{"id": id, "title": title, "ccliSongNo": ccli}],
        "recordedBy": {"id": "", "title": ""},
        "lyrics": {"print": 0, "digital": "1", "record": 0, "translate": 0},
        "sheetMusic": [], "rehearsals": [], "masterRecordings": []
    }
    return report_data


# if the script doesn\'t work, you need to re log into your ccli account,
# perform a search, and then a report and paste the chrome curl command of the report here:
#
# It will be a POST to https://reporting.ccli.com/api/report
#curl = '''curl 'https://reporting.ccli.com/api/search?searchTerm=7110639&searchCategory=all&searchFilters=\[\]'   -H 'Connection: keep-alive'   -H 'Accept: application/json, text/plain, */*'   -H 'client-locale: en-US'   -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'   -H 'Content-Type: application/json;charset=utf-8'   -H 'Sec-Fetch-Site: same-origin'   -H 'Sec-Fetch-Mode: cors'   -H 'Sec-Fetch-Dest: empty'   -H 'Referer: https://reporting.ccli.com/search?s=7110639&page=1&category=all'   -H 'Accept-Language: en-US,en;q=0.9,fr;q=0.8'   -H 'Cookie: _ga=GA1.2.1697472532.1602607883; _gid=GA1.2.366473120.1602607883; _hjTLDTest=1; _hjid=7b363541-fd55-482c-9890-4aa23ee835a2; ARRAffinity=fec4d939f30049bff6f938c61645390e2e68b0974922682d1cbb5a8acfa80f72; ARRAffinitySameSite=fec4d939f30049bff6f938c61645390e2e68b0974922682d1cbb5a8acfa80f72; _vwo_uuid_v2=DBB044809D5D6071A1B3727BB664D1466|8cc50bf4621ae545b08b649ac9376e30; CCLI_AUTH=5F47023AAFEAFE48F702E4C81AC13496C9DC36555EC08B0852E78BC4A8D2EDAC5ACFD3771424F95AAF1F4C6266C5C77D9D9832B236A1D4C4983799DB5FDBEFDF11C04CD4DA67601C64801252C84C8433516C1E9CD9794F7E95A7C1463DF874378A011CFB45A1AC3C2A3F17600C642C3CF2076BC4; CCLI_JWT_AUTH=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJQZXJzb25JZCI6IjBlMmU4MWUwLTU1ZjUtNDBmNC05NjI0LTk3OWU5ZDkyYzY2MyIsIk9yZ2FuaXphdGlvbklkIjoiZGFkYjAxZTEtOWQ4My00YWEzLWJjMTctMTAxN2E4Y2Y4YWNmIiwiT3JnYW5pemF0aW9uTmFtZSI6IkxhZmF5ZXR0ZSBDb21tdW5pdHkgQ2h1cmNoIiwiQXV0aFRva2VuIjoiOWJjZDUxY2MtZjQ2My00ZTU3LWI5MjktYTIxN2RkOTJlMjMxIiwiUGVyc2lzdExvZ2luIjoiVHJ1ZSIsIm5iZiI6MTYwMjYwNzk0MywiZXhwIjoxNjAzODE3NTQzLCJpYXQiOjE2MDI2MDc5NDMsImlzcyI6InByb2ZpbGUuY2NsaS5jb20iLCJhdWQiOiIuY2NsaS5jb20ifQ.20wLpm5Hj9cixoHJ98NNdbqg6IlKt6z68JKaE864EMY; .AspNetCore.Antiforgery.w5W7x28NAIs=CfDJ8CHFVy366qhHuD8o-Wi3XXzy8C7CMyD3D0cQWqinqn8RS5BL7oBg9rFDfBmdEHaiObtgjwfYzKMak3JVxPPPXHb6AZd6NM7Ys9gay_ptSqhuDHkudaSRjuLmAECNBJYltMKF5Xnpq2jPnbBmd8g9Iqo; .AspNetCore.Session=CfDJ8CHFVy366qhHuD8o%2BWi3XXx6UgCCm4A%2FwaDs%2BISBU5TUZ5EFSQxLjcUDmNwduMB8CckaZWF%2F0ZHXgPmHutxyJgpbepD6b3209475CpAmyrdebj%2FQWhz4k%2BKMmIiIeU5odjsZuGw%2Fv1X8HTjWPZgRxkokMJwfFogqihjBW474mg%2BR; _hjAbsoluteSessionInProgress=0' --compressed'''
curl = open('ccli-curl.config', 'r').read()
curl = curl.replace('\r', '\n').replace('\n\n', '\n').replace('\\\n', ' ')

# convert the curl command to headers and such
header_pairs = re.findall(r'-H \'(.*?):(.*?)\'', curl)
headers = {}
for k, v in header_pairs:
    headers[k] = v.strip()

song_details = 'https://reporting.ccli.com/api/detail/song/{}'
report_endpoint = 'https://reporting.ccli.com/api/report'


# now, here is the real procedure
load()
if 'last_report_timestamp' in history:
    last_report_timestamp = history['last_report_timestamp']
else:
    last_report_timestamp = 1601784000  # october 4, 2020

last_date = datetime.date.fromtimestamp(last_report_timestamp).strftime('%Y-%m-%d')
today = datetime.date.today().strftime('%Y-%m-%d')

toreport = []
lib = OpenSong.Library('/Volumes/Data/SEAFILE/LCC/LCC Worship Team/OpenSong')
for datestamp in lib.sets:
    songset = lib.sets[datestamp]
    if last_date < songset.name < today:
        print('\nREPORT NEEDED: ' + songset.name)
        for song in songset.songs:
            print(song.name)
            toreport.append(song.ccli)


# setup the session
sess = requests.Session()
sess.headers = headers

for ccli in toreport:
    print(f'SUBMITTING REPORT FOR {ccli}')
    r = sess.get(song_details.format(ccli))
    if r.status_code == 200:
        details = r.json()
        print(details)
        tosubmit = make_report_data(details['id'], details['title'], details['ccliSongNo'])
        r = sess.post(report_endpoint, json=tosubmit)
        print(r)
        print(r.headers)
        print(r.text)

history['last_report_timestamp'] = today
history[today] = toreport
save()
