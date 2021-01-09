#!/usr/bin/env python3
import os
import sys
from xml.etree import ElementTree as ET
import time
import json
import re
import csv


# SETUP GLOBAL VARIABLES
SET_SEARCH = re.compile(r'(\d{4})-(\d{2})-(\d{2})[\s-]*(.*)')
REPORT_YEAR = 2021

if len(sys.argv) > 1:
    REPORT_YEAR = int(sys.argv[1])

REPORT_START_DATE = "%d-01-01" % REPORT_YEAR
REPORT_END_DATE = "%d-01-01" % (REPORT_YEAR + 1)
IGNORE_WORDS = ['fusion', 'book']

basedir = '/Volumes/Data/SEAFILE/LCC/LCC Worship Team'
reportdir = os.path.join(basedir, 'Song Usage Reports')
opensong = os.path.join(basedir, 'OpenSong')
setsdir = os.path.join(opensong, 'Sets')
songsdir = os.path.join(opensong, 'Songs')


class OpenSongSet():

    def __init__(self, setpath):
        # print 'opening set:', setpath
        if not os.path.exists(setpath):
            return

        xml = ET.parse(setpath)
        root = xml.getroot()
        self.name = root.attrib['name']
        self.description = ''
        self.songs = []
        slide_groups = xml.find('slide_groups')
        for slide_group in slide_groups:
            if slide_group.attrib['type'] == 'song':
                name = slide_group.attrib['name']
                try:
                    subdir = slide_group.attrib['path']
                except:
                    subdir = ''
                if subdir != '':
                    self.songs.append(os.path.join(subdir, name))
                else:
                    self.songs.append(name)
        # print self.name
        # print self.songs


class OpenSongSong():
    data = {}
    name = ''
    lyrics = ''
    author = ''
    copyright = ''
    last_used = ''

    def __init__(self, songpath):
        # print 'opening song:', songpath
        if not os.path.exists(songpath):
            return
        xml = ET.parse(songpath)
        song = xml.getroot()

        self.data = {}
        for element in song:
            # print element.tag
            # print element.text
            # print element.attrib
            self.data[element.tag] = element.text
        self.name = self.data['title']
        self.lyrics = self.data['lyrics']
        self.author = self.data['author']
        self.copyright = self.data['copyright']


if __name__ == "__main__":
    # first we get the sets from the sets directory
    # then we sort by date and take the ones in the past year
    # then we grab each song in each set and create data objects like this
    # song object == { songname : {setdate, uses} }
    # set object == { setdate : [song objects] }
    #
    # then we create two lists: one list is all songs in descending order of uses
    # second list is most recent 16 sets
    sets = {}
    allsongs = {}
    recent_sets = []
    for root, dirs, files in os.walk(setsdir):
        for basename in files:
            pathname = os.path.join(root, basename)
            try:
                set = OpenSongSet(pathname)
            except:
                print("could not parse", basename)
                continue
            name = set.name
            lower = name.lower()
            should_ignore = False
            for word in IGNORE_WORDS:
                if word in lower:
                    should_ignore = True
            if should_ignore:
                continue

            namedata = SET_SEARCH.findall(name)
            if len(namedata) == 0:
                continue
            else:
                print(namedata)
                try:
                    datestamp = time.strptime("%s-%s-%s" % namedata[0][:3], "%Y-%m-%d")
                except ValueError:
                    continue
                set.description = namedata[0][-1]

            if datestamp < time.strptime(REPORT_START_DATE, "%Y-%m-%d"):
                continue

            if datestamp > time.strptime(REPORT_END_DATE, "%Y-%m-%d"):
                continue

            print("\nparsing songs from set:")
            print(name)
            print(time.strftime('%B %d, %Y', datestamp))
            print("===================================")

            ignore_remaining_songs_in_set = False
            songs_seen = []
            for song_relative_path in set.songs[:]:
                song_real_path = os.path.join(songsdir, song_relative_path)
                name = os.path.basename(song_real_path)

                # if we have already seen an "alternates" divider, we ignore the rest of the songs in this set.
                if ignore_remaining_songs_in_set:
                    set.songs.remove(song_relative_path)
                    continue

                # have we already seen this song in this set?
                if name in songs_seen:
                    set.songs.remove(song_relative_path)
                    continue

                songs_seen.append(name)

                # is this song an admin divider for unused "alternates"
                if 'ALTERNATES' in name:
                    print("-- ALTERNATES found. Ignoring remaining songs in this set. ---")
                    ignore_remaining_songs_in_set = True
                    set.songs.remove(song_relative_path)
                    continue

                # is this song an admin divider
                if '===' in name:
                    # print "IGNORED:", name
                    set.songs.remove(song_relative_path)
                    continue

                # if we got here, add this song to the report array
                print("ADDED:  ", name)
                song = OpenSongSong(song_real_path)
                if name not in allsongs:
                    allsongs[name] = {"uses": 1, 'author': song.author, 'copyright': song.copyright, 'last_used': datestamp}
                    allsongs[name]['last_used_string'] = f"{datestamp.tm_year}-{datestamp.tm_mon:02}-{datestamp.tm_mday:02}"
                else:
                    allsongs[name]['uses'] += 1
                    if (datestamp > allsongs[name]['last_used']):
                        allsongs[name]['last_used'] = datestamp
                        allsongs[name]['last_used_string'] = f"{datestamp.tm_year}-{datestamp.tm_mon:02}-{datestamp.tm_mday:02}"

            # print set.songs
            sets[datestamp] = set

    # WE SAVE THE RAW SONG REPORT DATA
    towrite = {'allsongs': allsongs, 'recent_sets': recent_sets}
    reportpath = os.path.join(reportdir, f'LCC Song Usage ({REPORT_YEAR}).json')
    open(reportpath, 'w').write(json.dumps(towrite, indent=2))

    # NOW, WE PREPARE THE HTML REPORT
    html = "<html><head><style>body{font-family:'Source Sans Pro';}</style><title>OpenSongReport %s</title></head><body>" % time.strftime('%c')

    # now we need to sort the sets into ascending order by date
    print("SETLISTS FROM %d" % REPORT_YEAR)
    html += '<div id="menu"><a href="#setlists">Setlists for %s</a> || <a href="#frequency">Song Frequency</a></div>' % REPORT_YEAR

    html += '<a name="setlists" />'
    html += '<div id="setlists">'
    html += '<h1>Setlists For %s</h1>\n' % REPORT_YEAR
    for datestamp in sorted(sets.keys()):
        set = sets[datestamp]
        print(time.strftime('%B %d, %Y', datestamp))
        html += '<h2>%s <small>%s</small></h2><ul>' % (time.strftime('%B %d, %Y', datestamp), set.description)

        print('===================================')
        print(set.songs)
        for song in set.songs:
            if '===' in song:
                continue
            name = os.path.basename(song)
            songdata = allsongs[name]
            # print "%s (%s / (c) %s)" % (name, songdata['author'] or 'Unknown', songdata['copyright'] or 'Unknown')
            html += '<li>%s</li>' % "%s (%s / (c) %s)" % (name, songdata['author'] or 'Unknown', songdata['copyright'] or 'Unknown')
        print()
        print()
        html += '</ul>\n'

    html += '</div> <!-- end setlists -->'

    html += '<a name="frequency" />'
    html += '<div id="frequency">'

    # now we need to sort the songs into descending order by uses
    print("")
    print("SONGS BY FREQUENCY")
    html += '<h1>Songs By Frequency</h1>\n<ul>'
    print('===================================')
    sorted_songs = sorted(allsongs.keys(), key=lambda y: (allsongs[y]['uses']), reverse=True)
    for songname in sorted_songs:
        if '===' in songname:
            continue
        songdata = allsongs[songname]
        statline = f'{songdata["uses"]} times {songname} (last time {songdata["last_used_string"]}) ({songdata["author"] or "Unknown"} / (c)  {songdata["copyright"] or "Unknown"})'
        print(statline)
        html += f'<li>{statline}</li>'

    html += '</ul></div></body></html>'
    reportname = "LCC Song Usage (%s).html" % REPORT_YEAR
    reportpath = os.path.join(reportdir, reportname)
    open(reportpath, 'w').write(html)

    # NOW WE PREPARE THE CSV USAGE REPORT
    reportname = "LCC Song Usage (%s).csv" % REPORT_YEAR
    reportpath = os.path.join(reportdir, reportname)
    with open(reportpath, 'w') as csvfile:
        report_writer = csv.writer(csvfile, delimiter=",", quotechar='"')
        report_writer.writerow(['Uses', 'Last Use', 'Song Name'])
        for songname in sorted_songs:
            if '===' in songname:
                continue
            uses = allsongs[songname]['uses']
            last_used = allsongs[songname]['last_used_string']
            report_writer.writerow([uses, last_used, songname])

    # exit()

    # AT YEAR END RUN THIS TOO
    # now add this report to the all songs report
    reportname = "LCC Song Usage (all).csv"
    reportpath = os.path.join(reportdir, reportname)
    with open(reportpath, 'r') as csvfile:
        report_reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        first_line = True
        for row in report_reader:
            if first_line:
                first_line = False
                continue
            count = int(row[0].replace('"', '').strip())
            last_used = row[1].strip().replace('"', '')
            name = row[2].strip().replace('"', '')

            if name in allsongs:
                allsongs[name]['uses'] += count
                if last_used > allsongs[name]['last_used_string']:
                    allsongs[name]['last_used_string'] = last_used
            else:
                allsongs[name] = {"uses": 1, 'last_used_string': last_used}

    # NOW WE PREPARE THE FINAL CSV USAGE REPORT
    towrite = 'Uses,Last Use,Song Name\n'
    sorted_songs = sorted(allsongs.keys(), key=lambda y: (allsongs[y]['uses']), reverse=True)

    reportname = "LCC Song Usage (all).csv"
    reportpath = os.path.join(reportdir, reportname)
    with open(reportpath, 'w') as csvfile:
        report_writer = csv.writer(csvfile, delimiter=",", quotechar='"')
        report_writer.writerow(['Uses', 'Last Use', 'Song Name'])
        for songname in sorted_songs:
            if '===' in songname:
                continue
            uses = allsongs[songname]['uses']
            last_used = allsongs[songname]['last_used_string']
            report_writer.writerow([uses, last_used, songname])
