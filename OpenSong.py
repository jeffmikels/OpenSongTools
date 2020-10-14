#!/usr/bin/env python3
import os
from xml.etree import ElementTree as ET
from datetime import datetime

librarypath = '/Volumes/Data/jeff/Dropbox/LCC/LCC Worship Team/OpenSong'
setsdir = ''
songsdir = ''


class Set():
    name = ''
    path = ''
    songs = []

    def __repr__(self):
        return '{}, {}, {}'.format(self.name, self.path, self.songs)

    def __init__(self, setpath):
        # print('opening set:', setpath)
        if not os.path.exists(setpath):
            return
        xml = ET.parse(setpath)
        root = xml.getroot()
        self.path = setpath
        self.name = root.attrib['name']
        self.songs = []
        slide_groups = xml.find('slide_groups')
        for slide_group in slide_groups:
            songpath = ''
            if slide_group.attrib['type'] == 'song':
                name = slide_group.attrib['name']
                try:
                    subdir = slide_group.attrib['path']
                except:
                    subdir = ''
                if subdir != '':
                    songpath = os.path.join(songsdir, subdir, name)
                else:
                    songpath = os.path.join(songsdir, name)
                if songpath != '':
                    # print(songpath)
                    song = Song(songpath)
                    # print(song.name)
                    if (song.name != ''):
                        self.songs.append(song)
        # print(self.name)
        # print(self.songs)


class Song():
    path = ''
    lyrics = ''
    name = ''
    ccli = ''
    data = {}

    def __init__(self, songpath):
        # print('opening song:', songpath)
        if not os.path.exists(songpath):
            return
        xml = ET.parse(songpath)
        song = xml.getroot()
        self.path = songpath

        self.data = {}
        for element in song:
            # print(element.tag)
            # print(element.text)
            # print(element.attrib)
            self.data[element.tag] = element.text
        self.name = self.data['title']
        self.lyrics = self.data['lyrics']
        self.ccli = self.data['ccli']


class Library():
    sets = {}
    songs = []
    songstats = {}

    def __init__(self, new_librarypath):
        global setsdir
        global songsdir
        global librarypath
        librarypath = new_librarypath

        setsdir = os.path.join(librarypath, 'Sets')
        songsdir = os.path.join(librarypath, 'Songs')

        # create sets listing
        for root, dirs, files in os.walk(setsdir):
            for basename in files:
                pathname = os.path.join(root, basename)
                try:
                    songset = Set(pathname)
                except:
                    # print("could not parse", basename)
                    continue
                name = songset.name

                try:
                    datestamp = datetime.strptime(name, "%Y-%m-%d")
                except:
                    continue
                if datestamp < datetime.strptime("2012-01-01", "%Y-%m-%d"):
                    continue

                self.sets[datestamp] = songset

                for song in songset.songs:
                    if song.path == '':
                        continue
                    self.songs.append(song)
                    songpath = song.path

                    name = os.path.basename(songpath)
                    if name not in self.songstats:
                        self.songstats[name] = {"uses": 1, 'author': song.data['author'], 'copyright': song.data['copyright']}
                    else:
                        self.songstats[name]['uses'] += 1


# if __name__ == "__main__":
#     # first we get the sets from the sets directory
#     # then we sort by date and take the ones in the past year
#     # then we grab each song in each set and create data objects like this
#     # song object == { songname : {setdate, uses} }
#     # set object == { setdate : [song objects] }
#     #
#     # then we create two lists: one list is all songs in descending order of uses
#     # second list is most recent 16 sets
#     sets = {}
#     allsongs = {}
#     recent_sets = []
#     for root, dirs, files in os.walk(setsdir):
#         for basename in files:
#             pathname = os.path.join(root, basename)
#             try:
#                 set = OpenSongSet(pathname)
#             except:
#                 print("could not parse", basename)
#                 continue
#             name = set.name
#             try:
#                 datestamp = time.strptime(name, "%Y-%m-%d")
#             except:
#                 continue
#             if datestamp < time.strptime("2012-01-01", "%Y-%m-%d"):
#                 continue

#             sets[datestamp] = set

#             for songbasename in set.songs:
#                 songpath = os.path.join(songsdir, songbasename)
#                 song = OpenSongSong(songpath)

#                 name = os.path.basename(songpath)
#                 if name not in allsongs:
#                     allsongs[name] = {"uses": 1, 'author': song.data['author'], 'copyright': song.data['copyright']}
#                 else:
#                     allsongs[name]['uses'] += 1

#     # NOW, WE PREPARE THE REPORT
#     html = "<html><head><title>OpenSongReport %s</title></head><body>" % time.strftime('%c')

#     # now we need to sort the sets into ascending order by date
#     print("SETLISTS THIS YEAR")
#     html += '<h1>Setlists This Year</h1>\n'
#     for datestamp in sorted(sets.iterkeys()):
#         print(time.strftime('%B %d, %Y', datestamp))
#         html += '<h2>%s</h2><ul>' % time.strftime('%B %d, %Y', datestamp)

#         print('===================================')
#         set = sets[datestamp]
#         for song in set.songs:
#             if '===' in song:
#                 continue
#             name = os.path.basename(song)
#             songdata = allsongs[name]
#             print("%s (%s / (c) %s)" % (name, songdata['author'] or 'Unknown', songdata['copyright'] or 'Unknown'))
#             html += '<li>%s</li>' % "%s (%s / (c) %s)" % (name, songdata['author'] or 'Unknown', songdata['copyright'] or 'Unknown')
#         print
#         print
#         html += '</ul>\n'

#     # now we need to sort the songs into descending order by uses
#     print("")
#     print("SONGS BY FREQUENCY")
#     html += '<h1>Songs By Frequency</h1>\n<ul>'
#     print('===================================')
#     sorted_songs = sorted(allsongs.keys(), key=lambda y: (allsongs[y]['uses']), reverse=True)
#     for songname in sorted_songs:
#         if '===' in songname:
#             continue
#         print('(%s times) %s (%s / (c)  %s)' % (allsongs[songname]['uses'], songname, songdata['author'] or 'Unknown', songdata['copyright'] or 'Unknown'))
#         html += '<li>(%s times) %s (%s / (c) %s)</li>' % (allsongs[songname]['uses'], songname, songdata['author'] or 'Unknown', songdata['copyright'] or 'Unknown')

#     html += '</ul></body></html>'
#     reportname = "LCC Song Usage for 2012.html"
#     reportpath = os.path.join(opensong, reportname)
#     open(reportpath, 'w').write(html)
